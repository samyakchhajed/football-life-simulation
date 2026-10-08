output "frontend_bucket_name" {
  value       = aws_s3_bucket.frontend.id
  description = "Name of the S3 bucket hosting frontend static assets"
}

output "website_endpoint" {
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
  description = "Website endpoint URL for the static frontend"
}

output "api_endpoint_url" {
  value       = aws_lambda_function_url.api_url.function_url
  description = "Public HTTPS endpoint URL of the API Lambda Function URL"
}

output "lambda_function_name" {
  value       = aws_lambda_function.api.function_name
  description = "Name of the API Lambda function"
}

output "lambda_function_arn" {
  value       = aws_lambda_function.api.arn
  description = "ARN of the API Lambda function"
}

