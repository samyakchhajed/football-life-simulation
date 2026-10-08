# ── ECR Repository for Worker Container Image ──────────────────────────────────
# Stores container images used by the EKS indexed batch generator pods.

resource "aws_ecr_repository" "worker" {
  name                 = "${var.project_name}-worker"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-worker"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "persistent-data"
  }
}

resource "aws_ecr_lifecycle_policy" "worker" {
  repository = aws_ecr_repository.worker.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images older than 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ── AWS Secrets Manager Secret for ECR Image URL ─────────────────────────────
# Stores ECR repository URL in Secrets Manager for retrieval into GitHub secrets and CLI use.

resource "aws_secretsmanager_secret" "ecr_image_url" {
  name                    = "${var.project_name}/ecr-image-url"
  description             = "ECR repository URL for worker container images"
  recovery_window_in_days = 0

  tags = {
    Name        = "${var.project_name}-ecr-image-url"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Layer       = "persistent-data"
  }
}

resource "aws_secretsmanager_secret_version" "ecr_image_url" {
  secret_id     = aws_secretsmanager_secret.ecr_image_url.id
  secret_string = aws_ecr_repository.worker.repository_url
}

