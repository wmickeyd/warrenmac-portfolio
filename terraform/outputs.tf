output "project_id" {
  description = "The GCP Project ID"
  value       = var.project_id
}

output "gke_cluster_name" {
  description = "Name of the provisioned GKE cluster"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "Kubernetes API control plane endpoint"
  value       = module.gke.endpoint
}

output "kubectl_connect_command" {
  description = "Execute this command to configure kubectl credentials for the cluster"
  value       = module.gke.get_credentials_command
}

output "gcs_resume_bucket" {
  description = "Google Cloud Storage bucket for resume upload and dynamic ingestion"
  value       = module.storage.bucket_name
}

output "gsa_workload_identity_email" {
  description = "Google Service Account email bound to Workload Identity"
  value       = module.iam.service_account_email
}

output "k8s_annotated_service_account" {
  description = "Kubernetes ServiceAccount manifest snippet with Workload Identity annotation"
  value       = <<-EOT
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: ${var.k8s_service_account}
      namespace: ${var.k8s_namespace}
      annotations:
        iam.gke.io/gcp-service-account: ${module.iam.service_account_email}
  EOT
}
