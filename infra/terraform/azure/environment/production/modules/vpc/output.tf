output "public_subnet_id" {
  value = aws_subnet.public_subnet.id
}
output "web_app_sg_id" {
  value = aws_security_group.web_app_sg.id
}
output "private_subnet_groups_name" {
  value = aws_db_subnet_group.private_subnet_groups.name
}

output "database_sg_id" {
  value = aws_security_group.database_sg.id
}