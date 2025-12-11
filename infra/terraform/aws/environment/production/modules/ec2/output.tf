output "ec2_public_ip" {
  value = aws_instance.web_app.public_ip
}

output "EC2_APP_SERVER_INSTANCE_ID" {
  value = aws_instance.web_app.id
}

output "ssh_key_secret_name" {
  value       = aws_secretsmanager_secret.ssh_private_key.name
  description = "Name of the Secrets Manager secret containing the SSH private key"
}
