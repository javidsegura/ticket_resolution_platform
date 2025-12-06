resource "random_string" "storage_postfix" {
  length  = 8
  special = false
  upper   = false
  numeric = true
}

resource "azurerm_storage_account" "storage_account" {
  name                     = "${lower(replace(substr("${var.environment}ai_ticket", 0, 16), "-", ""))}${random_string.storage_postfix.result}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  blob_properties {
    versioning_enabled = true

    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }
}

resource "azurerm_storage_container" "image_container" {
  name                  = "images"
  storage_account_name  = azurerm_storage_account.storage_account.name
  container_access_type = "blob"
}
