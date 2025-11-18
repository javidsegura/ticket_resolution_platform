output "storage_account_name" {
  value = azurerm_storage_account.sa.name
}

output "storage_container_name" {
  value = azurerm_storage_container.data.name
}

output "resource_group_name" {
  value = data.azurerm_resource_group.rg.name
}