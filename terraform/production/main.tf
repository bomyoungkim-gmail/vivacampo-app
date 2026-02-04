terraform {
  backend "s3" {
    bucket = "vivacampo-terraform-state"
    key    = "production/terraform.tfstate"
    region = "sa-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

module "ecs" {
  source      = "../modules/ecs"
  environment = "production"
}

module "rds" {
  source                 = "../modules/rds"
  environment            = "production"
  instance_class         = "db.r5.large"
  allocated_storage      = 100
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password
  subnet_ids             = var.db_subnet_ids
  vpc_security_group_ids = var.db_security_group_ids
  publicly_accessible    = false
  multi_az               = true
  skip_final_snapshot    = false
  backup_retention_period = 14
}

module "s3" {
  source      = "../modules/s3"
  environment = "production"
  buckets     = ["tiles", "mosaics", "exports"]
}

module "sqs" {
  source      = "../modules/sqs"
  environment = "production"
  queues      = ["jobs", "jobs-dlq"]
}
