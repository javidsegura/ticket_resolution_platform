

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket  = "ai-ticket-platform-remote-state-bucket-zxmluk37"
    key     = "remote-state/staging/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}


provider "aws" {
  region = var.main_region

  default_tags {
    tags = {
      Environment = var.environment
    }
  }
}


module "s3" {
  source = "../../modules/s3"

  environment  = var.environment
  main_region  = var.main_region
  project_name = var.project_name
}

module "vpc" {
  source = "./modules/vpc"

  main_region = var.main_region
}

module "ec2" {
  source = "./modules/ec2"

  # VPC
  ## SUBNETS
  public_subnet_id        = module.vpc.public_subnet_id
  private_subnet_sever_id = module.vpc.private_subnet_server_id
  ## SG
  web_app_sg_id = module.vpc.web_app_sg_id
  bastion_sg_id = module.vpc.bastion_sg_id
  # S3
  aws_s3_web_arn = module.s3.s3_bucket_arn
  # SECRETS
  aws_secretsmanager_database_crentials_arn = module.rds.aws_secretsmanager_database_crentials_arn
  # EC2
  instance_type_bastion = var.instance_type_bastion
  instance_type_web_app = var.instance_type_web_app
}

module "rds" {
  source = "../../modules/rds"

  db_username                = var.db_username
  database_sg_id             = module.vpc.db_sg_id
  private_subnet_groups_name = module.vpc.private_db_subnet_groups_name
  environment                = "staging"

}
