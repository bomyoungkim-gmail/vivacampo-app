variable "aws_region" {
  type    = string
  default = "sa-east-1"
}

variable "db_name" {
  type = string
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_subnet_ids" {
  type = list(string)
}

variable "db_security_group_ids" {
  type = list(string)
}
