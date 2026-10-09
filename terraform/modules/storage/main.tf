# Hardened GCS Bucket for Dynamic PDF Resume Ingestion
resource "google_storage_bucket" "resume_bucket" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.region
  force_destroy = var.force_destroy

  # Security Baseline: Uniform IAM, no public access
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  # Versioning: Retains audit history of uploaded resumes and allows rollbacks
  versioning {
    enabled = true
  }

  # Lifecycle: Automatically prune older versions after 90 days to save costs
  lifecycle_rule {
    condition {
      num_newer_versions = 5
      days_since_noncurrent_time = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = "production"
    managed_by  = "terraform"
    application = "warrenmac-portfolio"
  }
}

