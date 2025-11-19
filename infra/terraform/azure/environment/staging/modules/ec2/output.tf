
output "ec2_app_server_private_ip" {
  value = aws_instance.web_app.private_ip
}

output "ec2_bastion_server_public_ip" {
  value = aws_instance.bastion_host.public_ip
}

output "ec2_app_server_ssh_user" {
  value = "ec2-user"
}
output "ec2_bastion_server_ssh_user" {
  value = "ec2-user"
}