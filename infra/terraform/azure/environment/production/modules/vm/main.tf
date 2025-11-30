
# 1. SSH KEY PAIR GENERATION
resource "tls_private_key" "priv_key" {
  algorithm = "RSA"
  rsa_bits  = 4096 # Strong encryption
}

# Save the private key locally for Ansible/SSH access
resource "local_file" "private_key" {
  content         = tls_private_key.priv_key.private_key_pem
  filename        = var.ssh_key_local_path
  file_permission = "0400" # Read-only for owner (secure)
}


# 2. MANAGED IDENTITY (Azure's IAM Role)
resource "azurerm_user_assigned_identity" "vm_identity" {
  name                = "vm-managed-identity"
  location            = var.location
  resource_group_name = var.resource_group_name
}


# 3. NETWORKING FOR VM
resource "azurerm_public_ip" "vm_public_ip" {
  name                = "vm-public-ip"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static" # Static IP won't change on VM restart
  sku                 = "Standard"
}

# Network interface connects the VM to the subnet and assigns IPs
resource "azurerm_network_interface" "vm_nic" {
  name                = "vm-nic"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.public_subnet_id
    private_ip_address_allocation = "Dynamic" # Azure assigns private IP automatically
    public_ip_address_id          = azurerm_public_ip.vm_public_ip.id
  }
}

# Associate the Web App NSG with the NIC for firewall rules
resource "azurerm_network_interface_security_group_association" "vm_nsg_assoc" {
  network_interface_id      = azurerm_network_interface.vm_nic.id
  network_security_group_id = var.web_app_nsg_id
}

# Associate the VM's NIC with the Web App ASG
# This allows the database NSG to reference this VM in its rules
resource "azurerm_network_interface_application_security_group_association" "vm_asg_assoc" {
  network_interface_id          = azurerm_network_interface.vm_nic.id
  application_security_group_id = var.web_app_asg_id
}


# 4. VIRTUAL MACHINE
resource "azurerm_linux_virtual_machine" "web_app" {
  name                = "web-app-vm"
  location            = var.location
  resource_group_name = var.resource_group_name
  size                = "Standard_B2s" # ~2 vCPU, 4GB RAM (similar to t3.small)
  admin_username      = "azureuser"

  network_interface_ids = [
    azurerm_network_interface.vm_nic.id
  ]

  # Use SSH key authentication (no password)
  admin_ssh_key {
    username   = "azureuser"
    public_key = tls_private_key.priv_key.public_key_openssh
  }

  # OS disk configuration
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS" # Locally redundant storage
    disk_size_gb         = 30             # OS disk size
  }

  # Ubuntu 22.04 LTS image
  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  # Attach the managed identity to this VM
  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.vm_identity.id
    ]
  }

  # Disable password authentication (SSH keys only)
  disable_password_authentication = true
}


# 5. RBAC PERMISSIONS
# A) Grant VM identity permissions to read/write blob storage
resource "azurerm_role_assignment" "blob_contributor" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor" # Read, write, delete blobs
  principal_id         = azurerm_user_assigned_identity.vm_identity.principal_id
}

# B) Grant VM identity permissions to read secrets from Key Vault
resource "azurerm_role_assignment" "key_vault_secrets_user" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User" # Read secret values
  principal_id         = azurerm_user_assigned_identity.vm_identity.principal_id
}
