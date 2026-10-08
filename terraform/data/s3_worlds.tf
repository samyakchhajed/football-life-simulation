# ── Immutable S3 Bucket for Pre-Simulated World Templates ───────────────────────
# Rule: Generated worlds are never overwritten or deleted.
# No lifecycle purge or expiration rules.

resource "aws_s3_bucket" "world_templates" {
  bucket        = "${var.project_name}-templates-${var.aws_region}"
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-templates"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "persistent-data"
  }
}

resource "aws_s3_bucket_versioning" "world_templates" {
  bucket = aws_s3_bucket.world_templates.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "world_templates" {
  bucket = aws_s3_bucket.world_templates.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "world_templates" {
  bucket = aws_s3_bucket.world_templates.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
