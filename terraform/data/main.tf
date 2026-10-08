# ── Layer 2: Persistent Data (S3 World Templates, DynamoDB Catalog, ECR) ───────
# Applied by data.yml workflow. Apply-only. Never destroyed.

terraform {
  required_version = ">= 1.6.0"

  backend "s3" {}

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
