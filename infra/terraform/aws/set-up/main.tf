
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }
  required_version = ">= 1.2"
}

provider "aws" {
  region = "us-east-1"

}


resource "random_string" "random_postfix" {
  length  = 8
  special = false
  upper   = false
}

// Creating S3 bucket for state
resource "aws_s3_bucket" "remote_state_bucket" {
  bucket        = "${var.project_name}-remote-state-bucket-${random_string.random_postfix.result}"
  force_destroy = true
}




resource "aws_s3_bucket_versioning" "remote_state_bucket_versioning" {
  bucket = aws_s3_bucket.remote_state_bucket.id

  versioning_configuration {
    status = "Enabled"
  }

}

resource "aws_s3_bucket_lifecycle_configuration" "remote_state_lifecycle_conifg" {
  bucket = aws_s3_bucket.remote_state_bucket.id

  rule {
    id     = "state_lifecylce"
    status = "Enabled"

    filter {
      prefix = "remote-state/"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }


  }
}
