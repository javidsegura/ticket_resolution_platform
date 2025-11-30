
# 1. Virtual Network (VNet) - Equivalent to AWS VPC
resource "azurerm_virtual_network" "main_vnet" {
  name                = "main-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = var.location
  resource_group_name = var.resource_group_name
}

# 2. Subnets - Equivalent to AWS Subnets
resource "azurerm_subnet" "public_subnet" {
  name                 = "public-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "private_subnet" {
  name                 = "private-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main_vnet.name
  address_prefixes     = ["10.0.2.0/24"]

  # Delegate this subnet for MySQL Flexible Server
  delegation {
    name = "mysql-delegation"
    service_delegation {
      name = "Microsoft.DBforMySQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# 3. Route Tables (Equivalent to AWS Route Tables)
resource "azurerm_route_table" "public_route_table" {
  name                = "public-route-table"
  location            = var.location
  resource_group_name = var.resource_group_name

  route {
    name           = "default-internet-route"
    address_prefix = "0.0.0.0/0"
    next_hop_type  = "Internet"
  }
}

resource "azurerm_route_table" "private_route_table" {
  name                = "private-route-table"
  location            = var.location
  resource_group_name = var.resource_group_name

  # No internet route - private subnets only have local VNet routing
}

# 4. Route Table Associations
resource "azurerm_subnet_route_table_association" "public_rt_assoc" {
  subnet_id      = azurerm_subnet.public_subnet.id
  route_table_id = azurerm_route_table.public_route_table.id
}

# Note: Cannot associate route table with delegated subnet (private_subnet)
# Azure manages routing for subnets delegated to services like MySQL

# 5. Network Security Groups (Equivalent to AWS Security Groups)
# NSG for web application servers
resource "azurerm_network_security_group" "web_app_nsg" {
  name                = "web-app-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name

  # Allow HTTP from internet
  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow HTTPS from internet
  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Allow SSH for Ansible
  security_rule {
    name                       = "AllowSSH"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Azure allows all outbound by default, matching AWS egress rule
}

# Application Security Group - used to reference web app VMs in database NSG rules
resource "azurerm_application_security_group" "web_app_asg" {
  name                = "web-app-asg"
  location            = var.location
  resource_group_name = var.resource_group_name
}

# NSG for database servers
resource "azurerm_network_security_group" "database_nsg" {
  name                = "database-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name

  # Allow MySQL (3306) only from web app ASG
  # This is the Azure equivalent of AWS security_groups = [aws_security_group.web_app_sg.id]
  security_rule {
    name                                  = "AllowMySQL-From-WebApp"
    priority                              = 100
    direction                             = "Inbound"
    access                                = "Allow"
    protocol                              = "Tcp"
    source_port_range                     = "*"
    destination_port_range                = "3306"
    source_application_security_group_ids = [azurerm_application_security_group.web_app_asg.id]
    destination_address_prefix            = "*"
  }

  # Azure allows all outbound by default
}

# 6. Subnet-NSG Associations
resource "azurerm_subnet_network_security_group_association" "public_nsg_assoc" {
  subnet_id                 = azurerm_subnet.public_subnet.id
  network_security_group_id = azurerm_network_security_group.web_app_nsg.id
}

# Associate NSG with private subnet (delegated for MySQL)
# While Azure puts "Intent Policies" on the subnet, we must associate the NSG
# if we want the AllowMySQL-From-WebApp rule to actually work
resource "azurerm_subnet_network_security_group_association" "private_nsg_assoc" {
  subnet_id                 = azurerm_subnet.private_subnet.id
  network_security_group_id = azurerm_network_security_group.database_nsg.id
}
