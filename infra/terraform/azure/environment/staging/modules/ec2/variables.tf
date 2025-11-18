
# VPC
## SUBNETS
variable "public_subnet_id" {
  type = string
}
variable "private_subnet_sever_id" {
  type = string
}
## SG
variable "web_app_sg_id" {
  type = string
}
variable "bastion_sg_id" {
  type = string
}
# SSH 
variable "ssh_key_local_path" {
  type = string
}
# S3 
variable "aws_s3_web_arn" {
  type = string 
}
# SECRETS
variable "aws_secretsmanager_database_crentials_arn" {
  type = string
}
# EC2 
variable "instance_type_web_app" {
  type = string
}
variable "instance_type_bastion" {
  type = string
}

