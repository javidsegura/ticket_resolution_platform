
# Create username secret

resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$&*()-_=+[]{}<>?"

}

resource "random_string" "name" {
  length  = 4
  special = false
  upper   = false

}

resource "aws_secretsmanager_secret" "database_credentials" {
  name                    = "db-credentials-${var.environment}-${random_string.name.result}"
  description             = "RDS credentials for url-shortener"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "database_credentials_var" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
  })
}


resource "aws_db_instance" "database" {
  identifier             = "app-db"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.small"
  allocated_storage      = 10
  username               = var.db_username
  password               = random_password.db_password.result
  db_subnet_group_name   = var.private_subnet_groups_name
  vpc_security_group_ids = [var.database_sg_id]
  skip_final_snapshot    = true
  multi_az               = false

  tags = {
    Name = "private_database"
  }
}
