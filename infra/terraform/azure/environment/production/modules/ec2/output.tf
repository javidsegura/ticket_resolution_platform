output "ec2_public_ip" {
  value = aws_instance.web_app.public_ip
}
output "EC2_APP_SERVER_INSTANCE_ID" {
  value = aws_instance.web_app.id
}