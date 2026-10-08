# ── EKS Pod Identity for World Generation Workers ──────────────────────────────
# Rule: Put and read only to templates/v1/*. No delete, no overwrite.

resource "aws_iam_role" "worker_pod" {
  name = "${var.cluster_name}-worker-pod-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "pods.eks.amazonaws.com"
        }
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.cluster_name}-worker-pod-role"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_policy" "worker_permissions" {
  name        = "${var.cluster_name}-worker-permissions"
  description = "Scoped permissions for world-generation worker pods: S3 Put/Get on templates/v1/* and DynamoDB Put/Get on catalog"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3TemplateWriteAndRead"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.templates_bucket_name}/templates/v1/*"
        ]
      },
      {
        Sid    = "DynamoDBCatalogWriteAndRead"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.dynamodb_catalog_table_name}"
        ]
      }

    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_attach" {
  role       = aws_iam_role.worker_pod.name
  policy_arn = aws_iam_policy.worker_permissions.arn
}

resource "aws_eks_pod_identity_association" "worker" {
  cluster_name    = aws_eks_cluster.main.name
  namespace       = "worldgen"
  service_account = "worldgen-worker"
  role_arn        = aws_iam_role.worker_pod.arn

  depends_on = [
    aws_eks_addon.pod_identity,
    aws_eks_cluster.main
  ]
}
