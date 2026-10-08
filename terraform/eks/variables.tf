variable "aws_region" {
  type        = string
  description = "Target AWS deployment region"
  default     = "ap-south-1"
}

variable "project_name" {
  type        = string
  description = "Project name prefix for resources"
  default     = "football-life"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
  default     = "prod"
}

variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster"
  default     = "football-life-eks"
}

variable "cluster_version" {
  type        = string
  description = "Kubernetes version for the EKS cluster"
  default     = "1.34"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the EKS VPC"
  default     = "10.0.0.0/16"
}

variable "node_instance_types" {
  type        = list(string)
  description = "EC2 instance types for the EKS node group"
  default     = ["t3.medium"]
}


variable "owner_iam_user_arn" {
  type        = string
  description = "IAM user ARN of the cluster owner for PC kubectl admin access"
  default     = ""
}

variable "templates_bucket_name" {
  type        = string
  description = "Name of the Layer 2 S3 bucket storing world templates"
  default     = "football-life-templates-ap-south-1"
}

variable "dynamodb_catalog_table_name" {
  type        = string
  description = "Name of the Layer 2 DynamoDB template catalog table"
  default     = "world_template_catalog"
}
