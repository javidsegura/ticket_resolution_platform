output "storage_account_name" {
  value = azurerm_storage_account.storage_account.name
}

output "storage_account_id" {
  description = "ID of the storage account for RBAC role assignments"
  value       = azurerm_storage_account.storage_account.id
}

output "storage_container_name" {
  value = azurerm_storage_container.image_container.name
}
