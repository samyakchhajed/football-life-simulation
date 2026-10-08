# ── EKS Access Entry for Cluster Owner ──────────────────────────────────────────
# Grants the owner's IAM user cluster-admin access so kubectl works directly from PC.

resource "aws_eks_access_entry" "owner" {
  count         = var.owner_iam_user_arn != "" ? 1 : 0
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = var.owner_iam_user_arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "owner_admin" {
  count         = var.owner_iam_user_arn != "" ? 1 : 0
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = var.owner_iam_user_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.owner]
}
