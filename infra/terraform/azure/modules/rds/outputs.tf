output "rds_address" {
  value = aws_db_instance.database.address
}

output "db_crendentials_key" {
  value = aws_secretsmanager_secret.database_credentials.name
}
output "aws_secretsmanager_database_crentials_arn" {
  value = aws_secretsmanager_secret.database_credentials.arn
}