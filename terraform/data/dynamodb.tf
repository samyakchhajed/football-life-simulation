# ── DynamoDB Template Catalog Table ─────────────────────────────────────────
# Stores metadata, quality gate audit results, and S3 URIs for 100-season templates.
# No user records or account data.

resource "aws_dynamodb_table" "template_catalog" {
  name         = "world_template_catalog"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "template_id"
  range_key    = "seed"

  attribute {
    name = "template_id"
    type = "S"
  }

  attribute {
    name = "seed"
    type = "N"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "world-template-catalog"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "persistent-data"
  }
}
