

terraform {
  required_providers {
    azurerm = { 
      source = "hashicorp/azurerm" 
    version = "~> 3.0" # Use a modern version}
    }
  }
  backend "azurerm" {
    resource_group_name  = "BCSAI2025-DEVOPS-STUDENT-2A"
    storage_account_name = "urlshortenertfsznytxoti"
    container_name       = "remote-state-data"
    key                  = "dev/terraform.tfstate"    
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id # A subscription is your billing boundary. Policies, access controll applied 
}

module "blob_storage" {
  source = "../../modules/blob_storage"

  environment = var.environment
  location = var.location
  resource_group_name = var.resource_group_name
  
}