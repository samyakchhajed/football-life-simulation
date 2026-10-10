# ── Layer 4: Lambda API Function & Public Function URL ─────────────────────────
# Serves the FastAPI simulation engine for user careers.
# Reads 100-season world templates from Layer 2 S3 and persists active player saves.

locals {
  templates_bucket = var.templates_bucket_name != "" ? var.templates_bucket_name : "${var.project_name}-templates-${var.aws_region}"
  function_name    = "${var.project_name}-api-${var.environment}"
  package_path     = var.lambda_package_path != "" ? var.lambda_package_path : (fileexists("${path.module}/build/lambda_package.zip") ? "${path.module}/build/lambda_package.zip" : data.archive_file.lambda_fallback.output_path)
}

# ── Fallback Archive (Source Only, used when prebuilt package is absent) ──────
data "archive_file" "lambda_fallback" {
  type        = "zip"
  output_path = "${path.module}/build/lambda_fallback.zip"

  source {
    content  = file("${path.module}/../../src/api/lambda_handler.py")
    filename = "src/api/lambda_handler.py"
  }

  source {
    content  = file("${path.module}/../../src/api/main.py")
    filename = "src/api/main.py"
  }

  source {
    content  = file("${path.module}/../../src/api/storage.py")
    filename = "src/api/storage.py"
  }
}

# ── IAM Role for Lambda Execution ─────────────────────────────────────────────

resource "aws_iam_role" "lambda_exec" {
  name = "${local.function_name}-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${local.function_name}-role"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "webapp"
  }
}

# Managed policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Scoped policy for S3 templates, saves & DynamoDB catalog access
resource "aws_iam_policy" "lambda_storage_access" {
  name        = "${local.function_name}-storage-policy"
  description = "Allows Lambda to read world templates and save active game states"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3TemplateAndSaveAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${local.templates_bucket}",
          "arn:aws:s3:::${local.templates_bucket}/*"
        ]
      },
      {
        Sid    = "DynamoDBCatalogRead"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:BatchGetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_catalog_table_name}"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_storage_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_storage_access.arn
}

# ── Lambda Function ────────────────────────────────────────────────────────────

resource "aws_lambda_function" "api" {
  function_name    = local.function_name
  role             = aws_iam_role.lambda_exec.arn
  handler          = "src.api.lambda_handler.handler"
  runtime          = "python3.11"
  filename         = local.package_path
  source_code_hash = filebase64sha256(local.package_path)
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout

  environment {
    variables = {
      TEMPLATES_S3_BUCKET    = local.templates_bucket
      SAVES_S3_BUCKET        = local.templates_bucket
      DYNAMODB_CATALOG_TABLE = var.dynamodb_catalog_table_name
      STORAGE_BACKEND        = "s3"
      ENVIRONMENT            = var.environment
      AWS_REGION_NAME        = var.aws_region
    }
  }

  tags = {
    Name        = local.function_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "webapp"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_storage_attachment
  ]
}

# ── Lambda Function URL (Zero-Cost HTTP Ingress with CORS) ─────────────────────

resource "aws_lambda_function_url" "api_url" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["*"]
    max_age           = 86400
  }
}

resource "aws_lambda_permission" "public_function_url" {
  statement_id           = "FunctionURLAllowPublicAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.api.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
