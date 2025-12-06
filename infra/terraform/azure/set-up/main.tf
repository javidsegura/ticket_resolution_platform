
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.2"
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id

}

data "azurerm_resource_group" "rg" {
  name = "BCSAI2025-DEVOPS-STUDENT-2A"
}

resource "random_string" "random_postfix" {
  length  = 8
  special = false
  upper   = false
  numeric = true
}

// Creating storage account
resource "azurerm_storage_account" "sa" {
  name                     = "${lower(replace(substr("tfstate${var.project_name}", 0, 16), "-", ""))}${random_string.random_postfix.result}"
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  blob_properties {
    versioning_enabled = true
  }
}

// Create blob container inside the s.a
resource "azurerm_storage_container" "data" {
  name                  = "remote-state-data"
  storage_account_name  = azurerm_storage_account.sa.name
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "remote_state_lifecycle" {
  storage_account_id = azurerm_storage_account.sa.id

  rule {
    name    = "tfstate_version_cleanup"
    enabled = true
    filters {
      blob_types = ["blockBlob"]

      prefix_match = ["remote_state_data/"]
    }

    actions {
      version {
        tier_to_archive_after_days_since_last_tier_change_greater_than = 30
        delete_after_days_since_creation                               = 365
      }
    }
  }
}
