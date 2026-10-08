# ── Layer 1: Terraform Bootstrap (Remote State S3 Bucket + DynamoDB Lock Table) ─
# Automated by GitHub Actions via OIDC, or applied locally.

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0, < 7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type        = string
  description = "Target AWS deployment region"
  default     = "ap-south-1"
}

variable "state_bucket_name" {
  type        = string
  description = "Name of the S3 bucket used for remote Terraform state"
  default     = "football-life-tfstate-ap-south-1"
}

variable "lock_table_name" {
  type        = string
  description = "Name of the DynamoDB table used for Terraform state locking"
  default     = "football-life-tfstate-locks"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket        = var.state_bucket_name
  force_destroy = false

  tags = {
    Name        = "Terraform Remote State"
    Environment = "global"
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Locks"
    Environment = "global"
    ManagedBy   = "Terraform"
  }
}

output "state_bucket_name" {
  value       = aws_s3_bucket.terraform_state.id
  description = "Remote S3 state bucket name"
}

output "lock_table_name" {
  value       = aws_dynamodb_table.terraform_locks.name
  description = "Remote DynamoDB state locking table name"
}
