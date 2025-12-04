output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = azurerm_public_ip.vm_public_ip.ip_address
}

output "vm_id" {
  description = "ID of the virtual machine"
  value       = azurerm_linux_virtual_machine.web_app.id
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = azurerm_network_interface.vm_nic.private_ip_address
}

output "managed_identity_id" {
  description = "ID of the managed identity attached to the VM"
  value       = azurerm_user_assigned_identity.vm_identity.id
}
