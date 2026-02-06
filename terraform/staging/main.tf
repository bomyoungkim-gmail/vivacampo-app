terraform {
  backend "s3" {
    bucket = "vivacampo-terraform-state"
    key    = "staging/terraform.tfstate"
    region = "sa-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

module "ecs" {
  source      = "../modules/ecs"
  environment = "staging"
}

module "rds" {
  source                 = "../modules/rds"
  environment            = "staging"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password
  subnet_ids             = var.db_subnet_ids
  vpc_security_group_ids = var.db_security_group_ids
  publicly_accessible    = false
  multi_az               = false
  skip_final_snapshot    = true
}

module "s3" {
  source      = "../modules/s3"
  environment = "staging"
  buckets     = ["tiles", "mosaics", "exports"]
}

module "sqs" {
  source      = "../modules/sqs"
  environment = "staging"
  queues      = ["jobs", "jobs-dlq"]
}
