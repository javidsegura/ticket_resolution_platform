output "database_fqdn" {
  description = "Fully qualified domain name of the MySQL server"
  value       = azurerm_mysql_flexible_server.database.fqdn
}

output "key_vault_id" {
  description = "ID of the Key Vault for RBAC role assignments"
  value       = azurerm_key_vault.vault.id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.vault.name
}

output "db_credentials_secret_name" {
  description = "Name of the secret containing database credentials"
  value       = azurerm_key_vault_secret.db_credentials.name
}
