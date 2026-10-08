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

variable "templates_bucket_name" {
  type        = string
  description = "Name of the Layer 2 persistent S3 bucket storing world templates. If empty, defaults to <project_name>-templates-<aws_region>"
  default     = ""
}

variable "dynamodb_catalog_table_name" {
  type        = string
  description = "Name of the DynamoDB template catalog table"
  default     = "world_template_catalog"
}

variable "lambda_memory_size" {
  type        = number
  description = "Memory allocation for the API Lambda function in MB"
  default     = 1024
}

variable "lambda_timeout" {
  type        = number
  description = "Execution timeout for the API Lambda function in seconds"
  default     = 30
}

variable "lambda_package_path" {
  type        = string
  description = "Custom prebuilt zip path for Lambda package. If empty, Terraform builds the package."
  default     = ""
}
