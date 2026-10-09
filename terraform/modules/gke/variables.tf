variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for the GKE cluster"
  type        = string
}

variable "cluster_name" {
  description = "The name of the GKE cluster"
  type        = string
  default     = "portfolio-cluster"
}

variable "network" {
  description = "VPC network name or ID"
  type        = string
}

variable "subnetwork" {
  description = "Subnet name or ID"
  type        = string
}

variable "pods_range_name" {
  description = "Name of secondary IP range for Pods"
  type        = string
  default     = "gke-pods"
}

variable "services_range_name" {
  description = "Name of secondary IP range for Services"
  type        = string
  default     = "gke-services"
}

variable "enable_autopilot" {
  description = "Whether to use GKE Autopilot mode (recommended for automated security hardening)"
  type        = bool
  default     = true
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for the GKE master control plane"
  type        = string
  default     = "172.16.0.0/28"
}

variable "deletion_protection" {
  description = "Whether deletion protection is enabled on the cluster"
  type        = bool
  default     = false
}

