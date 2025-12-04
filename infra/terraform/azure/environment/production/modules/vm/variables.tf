variable "location" {
  description = "Azure region for the VM"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "public_subnet_id" {
  description = "ID of the public subnet where VM will be deployed"
  type        = string
}

variable "web_app_nsg_id" {
  description = "ID of the Network Security Group for web app"
  type        = string
}

variable "web_app_asg_id" {
  description = "ID of the Application Security Group for web app"
  type        = string
}

variable "ssh_key_local_path" {
  description = "Local path to save the SSH private key"
  type        = string
}

variable "storage_account_id" {
  description = "ID of the storage account for blob access"
  type        = string
}

variable "key_vault_id" {
  description = "ID of the Key Vault for secrets access"
  type        = string
}
