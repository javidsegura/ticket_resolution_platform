output "ec2_app_server_private_ip" {
  value = module.ec2.ec2_app_server_private_ip
}

output "ec2_bastion_server_public_ip" {
  value = module.ec2.ec2_bastion_server_public_ip
}

output "ec2_app_server_ssh_user" {
  value = module.ec2.ec2_app_server_ssh_user
}

output "ec2_bastion_server_ssh_user" {
  value = module.ec2.ec2_bastion_server_ssh_user
}

output "ssh_key_secret_name" {
  value       = module.ec2.ssh_key_secret_name
  description = "Name of the Secrets Manager secret containing the SSH private key"
}

output "s3_main_bucket_name" {
  value = module.s3.s3_bucket_name
}

output "secrets_manager_db_credentials_key" {
  value = module.rds.db_crendentials_key
}

output "rds_mysql_host" {
  value = module.rds.rds_address
}

output "aws_main_region" {
  value = var.main_region
}
