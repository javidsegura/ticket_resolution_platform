terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0" # Use a modern version}
    }
  }
  backend "azurerm" {
    resource_group_name  = "BCSAI2025-DEVOPS-STUDENT-2A"
    storage_account_name = "urlshortenertfsznytxoti"
    container_name       = "remote-state-data"
    key                  = "prod/terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id # A subscription is your billing boundary. Policies, access controll applied
}


module "network" {
  source = "./modules/network"

  location            = var.location
  resource_group_name = var.resource_group_name
}

module "blob_storage" {
  source = "../../modules/blob_storage"

  environment         = var.environment
  location            = var.location
  resource_group_name = var.resource_group_name
}

module "mysql_db" {
  source = "../../modules/mysql_db"

  environment         = var.environment
  project_name        = var.project_name
  location            = var.location
  resource_group_name = var.resource_group_name
  db_username         = var.db_username
  delegated_subnet_id = module.network.delegated_subnet_id
  vnet_id             = module.network.vnet_id

  depends_on = [module.network]
}

module "vm" {
  source = "./modules/vm"

  location            = var.location
  resource_group_name = var.resource_group_name
  public_subnet_id    = module.network.public_subnet_id
  web_app_nsg_id      = module.network.web_app_nsg_id
  web_app_asg_id      = module.network.web_app_asg_id
  ssh_key_local_path  = var.ssh_key_local_path
  storage_account_id  = module.blob_storage.storage_account_id
  key_vault_id        = module.mysql_db.key_vault_id

  depends_on = [module.network, module.blob_storage, module.mysql_db]
}
