variable "project_id" {
  description = "The Google Cloud Project ID to deploy resources into"
  type        = string
}

variable "region" {
  description = "The Google Cloud region for infrastructure deployment"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
  default     = "portfolio-cluster"
}

variable "network_name" {
  description = "The name of the custom VPC network"
  type        = string
  default     = "portfolio-vpc"
}

variable "resume_bucket_name" {
  description = "Name for the Google Cloud Storage bucket storing the PDF resume (globally unique)"
  type        = string
  default     = ""
}

variable "enable_autopilot" {
  description = "Deploy GKE in Autopilot mode (recommended for automated security hardening)"
  type        = bool
  default     = true
}

variable "k8s_namespace" {
  description = "Kubernetes namespace for the portfolio application"
  type        = string
  default     = "portfolio"
}

variable "k8s_service_account" {
  description = "Kubernetes ServiceAccount name for Workload Identity binding"
  type        = string
  default     = "portfolio-agent"
}

