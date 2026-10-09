variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the Cloud Storage bucket"
  type        = string
}

variable "bucket_name" {
  description = "Name of the GCS bucket for resume storage"
  type        = string
}

variable "force_destroy" {
  description = "Allow bucket deletion even if non-empty (useful for demo/cleanup)"
  type        = bool
  default     = false
}
