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
