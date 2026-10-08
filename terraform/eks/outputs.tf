output "cluster_name" {
  value       = aws_eks_cluster.main.name
  description = "Name of the EKS cluster"
}

output "cluster_endpoint" {
  value       = aws_eks_cluster.main.endpoint
  description = "Endpoint for the EKS cluster API server"
}

output "cluster_certificate_authority_data" {
  value       = aws_eks_cluster.main.certificate_authority[0].data
  description = "Base64 encoded certificate data required to communicate with the cluster"
}

output "cluster_security_group_id" {
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  description = "Security group ID attached to the EKS cluster control plane"
}

output "cloudwatch_log_group_name" {
  value       = aws_cloudwatch_log_group.cluster.name
  description = "CloudWatch log group name for cluster control plane logging"
}

output "worker_pod_role_arn" {
  value       = aws_iam_role.worker_pod.arn
  description = "ARN of the IAM role assigned to world-generation worker pods via Pod Identity"
}

output "configure_kubectl_command" {
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
  description = "Command to configure kubectl on your local PC"
}
