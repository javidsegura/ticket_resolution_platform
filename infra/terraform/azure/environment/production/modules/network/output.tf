output "vnet_id" {
  description = "The ID of the Virtual Network"
  value       = azurerm_virtual_network.main_vnet.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = azurerm_subnet.public_subnet.id
}

output "private_subnet_id" {
  description = "The ID of the private subnet (delegated for MySQL)"
  value       = azurerm_subnet.private_subnet.id
}

output "delegated_subnet_id" {
  description = "The ID of the delegated subnet for MySQL Flexible Server"
  value       = azurerm_subnet.private_subnet.id
}

output "web_app_nsg_id" {
  description = "The ID of the web application Network Security Group"
  value       = azurerm_network_security_group.web_app_nsg.id
}

output "database_nsg_id" {
  description = "The ID of the database Network Security Group"
  value       = azurerm_network_security_group.database_nsg.id
}

output "web_app_asg_id" {
  description = "The ID of the web application Application Security Group"
  value       = azurerm_application_security_group.web_app_asg.id
}
