
variable "environment" {
  type = string
}

variable "project_name" {
  type = string
}
variable "location" {
  type = string
}
variable "resource_group_name" {
  type = string
}
variable "db_username" {
  type = string
}
variable "delegated_subnet_id" {
  type = string
}
variable "vnet_id" {
  type        = string
  description = "The ID of the Virtual Network to link the Private DNS Zone"
}
