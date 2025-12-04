

# Create username secret
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$&*()-_=+[]{}<>?"

}

resource "random_string" "name" {
  length  = 4
  special = false
  upper   = false

}

data "azurerm_client_config" "current" {}

locals {
  # Create alphanumeric-only segments for Key Vault name (max 24 chars total)
  env_short     = substr(replace(lower(var.environment), "/[^a-z0-9]/", ""), 0, 4)
  project_short = substr(replace(lower(var.project_name), "/[^a-z0-9]/", ""), 0, 6)
}

# Create the Private DNS Zone for MySQL
resource "azurerm_private_dns_zone" "mysql_dns_zone" {
  name                = "${var.project_name}.mysql.database.azure.com"
  resource_group_name = var.resource_group_name
}

# Link the DNS Zone to the Main VNet
resource "azurerm_private_dns_zone_virtual_network_link" "mysql_vnet_link" {
  name                  = "mysql-vnet-link"
  private_dns_zone_name = azurerm_private_dns_zone.mysql_dns_zone.name
  virtual_network_id    = var.vnet_id
  resource_group_name   = var.resource_group_name
}

resource "azurerm_key_vault" "vault" {
  name                = "kv${local.env_short}${local.project_short}${random_string.name.result}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id

  sku_name = "standard"

  soft_delete_retention_days = 90
  purge_protection_enabled   = true

  enable_rbac_authorization = true

}

resource "azurerm_role_assignment" "key_vault_secrets_officer" {
  scope                = azurerm_key_vault.vault.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_key_vault_secret" "db_credentials" {
  name         = "db-credentials-${var.environment}-${random_string.name.result}"
  key_vault_id = azurerm_key_vault.vault.id

  value = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
  })

  depends_on = [azurerm_role_assignment.key_vault_secrets_officer]
}

resource "azurerm_mysql_flexible_server" "database" {
  name                = "${var.project_name}-db-${random_string.name.result}"
  resource_group_name = var.resource_group_name
  location            = var.location
  version             = "8.0.21"

  sku_name = "B_Standard_B1s" # Basic tier, more widely supported
  storage {
    size_gb           = 20
    auto_grow_enabled = true
  }

  administrator_login    = var.db_username
  administrator_password = random_password.db_password.result

  delegated_subnet_id = var.delegated_subnet_id

  # Associate with Private DNS Zone for VNet resolution
  private_dns_zone_id = azurerm_private_dns_zone.mysql_dns_zone.id

  backup_retention_days = 7

  depends_on = [azurerm_private_dns_zone_virtual_network_link.mysql_vnet_link]

  lifecycle {
    ignore_changes = [
      zone # Zone cannot be changed after creation
    ]
  }
}

# Disable require_secure_transport
resource "azurerm_mysql_flexible_server_configuration" "require_secure_transport" {
  name                = "require_secure_transport"
  resource_group_name = var.resource_group_name
  server_name         = azurerm_mysql_flexible_server.database.name
  value               = "OFF"
}
