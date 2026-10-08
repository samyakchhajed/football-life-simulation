output "templates_bucket_name" {
  value       = aws_s3_bucket.world_templates.id
  description = "Name of the persistent S3 bucket storing world templates"
}

output "templates_bucket_arn" {
  value       = aws_s3_bucket.world_templates.arn
  description = "ARN of the persistent S3 bucket storing world templates"
}

output "dynamodb_catalog_table_name" {
  value       = aws_dynamodb_table.template_catalog.name
  description = "Name of the DynamoDB template catalog table"
}

output "dynamodb_catalog_table_arn" {
  value       = aws_dynamodb_table.template_catalog.arn
  description = "ARN of the DynamoDB template catalog table"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.worker.repository_url
  description = "Repository URL of the worker ECR container registry"
}

output "ecr_repository_name" {
  value       = aws_ecr_repository.worker.name
  description = "Repository name of the worker ECR container registry"
}

output "ecr_image_url_secret_arn" {
  value       = aws_secretsmanager_secret.ecr_image_url.arn
  description = "ARN of the Secrets Manager secret storing the ECR image URL"
}

output "ecr_image_url_secret_name" {
  value       = aws_secretsmanager_secret.ecr_image_url.name
  description = "Name of the Secrets Manager secret storing the ECR image URL"
}

