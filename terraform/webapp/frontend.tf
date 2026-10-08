# ── Frontend S3 Static Web App Hosting ─────────────────────────────────────────
# Destroyable along with Layer 4 webapp without affecting Layer 2 persistent data.

resource "aws_s3_bucket" "frontend" {
  bucket        = "${var.project_name}-frontend-${var.aws_region}"
  force_destroy = true

  tags = {
    Name        = "${var.project_name}-frontend"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "webapp"
  }
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_public_read" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}
