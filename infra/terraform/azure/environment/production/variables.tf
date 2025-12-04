variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
}

variable "db_username" {
  description = "MySQL database administrator username"
  type        = string
}

variable "ssh_key_local_path" {
  description = "Local path to save the SSH private key for VM access"
  type        = string
  default     = "~/.ssh/azure-vm-production-key.pem"
}
