# SUBNETS
output "public_subnet_id" {
  value = aws_subnet.public_subnet_bastion_a.id
}
output "private_subnet_server_id" {
  value = aws_subnet.private_subnet_server_a.id
}
output "private_db_subnet_groups_name" {
  value = aws_db_subnet_group.private_subnet_groups.name
}
# SECURITY GROUPS
output "bastion_sg_id" {
  value = aws_security_group.bastion_host_sg.id
}
output "web_app_sg_id" {
  value = aws_security_group.web_app_sg.id
}
output "db_sg_id" {
  value = aws_security_group.database_sg.id
}
