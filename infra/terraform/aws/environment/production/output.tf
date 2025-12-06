# Naming convention: <service_name>_<group>_<name>

output "s3_main_bucket_name" {
  value = module.s3.s3_bucket_name
}
output "rds_mysql_host" {
  value = module.rds.rds_address
}
output "ec2_app_server_public_ip" {
  value = module.ec2.ec2_public_ip
}
output "ec2_app_server_ssh_user" {
  value = "ec2-user"
}
output "ec2_servers_ssh_private_key_file_path" {
  value = abspath(pathexpand(var.ssh_key_local_path))
}

output "secrets_manager_db_credentials_key" {
  value = module.rds.db_crendentials_key
}

output "EC2_APP_SERVER_INSTANCE_ID" {
  value = module.ec2.EC2_APP_SERVER_INSTANCE_ID
}
output "aws_main_region" {
  value = var.main_region
}
