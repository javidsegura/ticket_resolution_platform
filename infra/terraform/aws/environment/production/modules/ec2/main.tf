
resource "aws_instance" "web_app" {
  ami                    = "ami-08982f1c5bf93d976"
  instance_type          = "t3.small"
  subnet_id              = var.public_subnet_id
  vpc_security_group_ids = [var.web_app_sg_id]
  key_name               = aws_key_pair.key_pair_ssh.key_name

  iam_instance_profile = aws_iam_instance_profile.web_app_profile.name

  root_block_device {
    volume_size = 8
  }

  tags = {
    Name = "public_web_server"
  }
}

# Creating SSH key pair
resource "tls_private_key" "priv_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}
resource "aws_key_pair" "key_pair_ssh" {
  key_name   = "ssh_key"
  public_key = tls_private_key.priv_key.public_key_openssh
}

# Store SSH key in Secrets Manager (single source of truth)
resource "random_string" "ssh_key_suffix" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_secretsmanager_secret" "ssh_private_key" {
  name                    = "ec2-ssh-private-key-production-${random_string.ssh_key_suffix.result}"
  description             = "SSH private key for EC2 instances in production"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "ssh_private_key" {
  secret_id     = aws_secretsmanager_secret.ssh_private_key.id
  secret_string = tls_private_key.priv_key.private_key_pem
}

# IAM ROLES
# Policy allowing EC2 to assume this role (Trust Policy)
data "aws_iam_policy_document" "assume_role" {
  statement {
    sid = "AllowEC2ToAssumeRole"
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# IAM Role for EC2 instance
resource "aws_iam_role" "app_server_role" {
  name               = "app_server_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# IAM Instance Profile to attach the role to the EC2 instance
resource "aws_iam_instance_profile" "web_app_profile" {
  name = "web_app_profile"
  role = aws_iam_role.app_server_role.name
}

# == POLICIES ==
# A) Policy defining S3 permissions
data "aws_iam_policy_document" "s3_access_policy" {
  statement {
    sid = "S3ReadAndPut"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = ["${var.aws_s3_web_arn}/*"]
  }
}

resource "aws_iam_policy" "s3_read_put_policy" {
  name        = "S3_Read_Put_Policy"
  description = "A policy that allows S3 read and put access."
  policy      = data.aws_iam_policy_document.s3_access_policy.json
}

resource "aws_iam_role_policy_attachment" "s3_attachment" {
  role       = aws_iam_role.app_server_role.name
  policy_arn = aws_iam_policy.s3_read_put_policy.arn
}

# B) Secret manager
data "aws_iam_policy_document" "secret_manager_access_policy" {
  statement {
    sid = "SecretsManagerAccessSecret"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      var.aws_secretsmanager_database_crentials_arn,
      aws_secretsmanager_secret.ssh_private_key.arn
    ]
  }
}

resource "aws_iam_policy" "get_secret_value" {
  name        = "Secrets_manager_get_secret_value"
  description = "Policy that allows getting secret values from Secrets Manager"
  policy      = data.aws_iam_policy_document.secret_manager_access_policy.json
}

# Attaching the secrets manager policy to the IAM Role
resource "aws_iam_role_policy_attachment" "secrets_manager_attachment" {
  role       = aws_iam_role.app_server_role.name
  policy_arn = aws_iam_policy.get_secret_value.arn
}
