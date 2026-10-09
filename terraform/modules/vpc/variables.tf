variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for VPC subnets"
  type        = string
}

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "portfolio-vpc"
}

variable "subnet_name" {
  description = "Name of the GKE node subnet"
  type        = string
  default     = "portfolio-gke-subnet"
}

variable "nodes_cidr" {
  description = "Primary CIDR block for GKE nodes"
  type        = string
  default     = "10.10.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary CIDR block for Kubernetes Pods"
  type        = string
  default     = "10.48.0.0/14"
}

variable "services_cidr" {
  description = "Secondary CIDR block for Kubernetes Services"
  type        = string
  default     = "10.52.0.0/20"
}
