variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "resume_bucket_name" {
  description = "The name of the GCS bucket storing the resume"
  type        = string
}

variable "k8s_namespace" {
  description = "Kubernetes namespace where the application runs"
  type        = string
  default     = "portfolio"
}

variable "k8s_service_account" {
  description = "Kubernetes ServiceAccount name for the portfolio pod"
  type        = string
  default     = "portfolio-agent"
}

variable "service_account_id" {
  description = "ID of the Google Service Account (GSA) for Workload Identity"
  type        = string
  default     = "portfolio-agent-sa"
}
