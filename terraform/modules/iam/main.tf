# Dedicated Google Service Account (GSA) for the Portfolio Agent
resource "google_service_account" "portfolio_agent" {
  account_id   = var.service_account_id
  display_name = "Portfolio Agent Workload Identity GSA"
  description  = "Least-privilege service account used by the GKE portfolio agent pod"
  project      = var.project_id
}

# 1. Least Privilege GCS Access: Read-only access strictly to the resume bucket
resource "google_storage_bucket_iam_member" "resume_reader" {
  bucket = var.resume_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.portfolio_agent.email}"
}

# 2. Workload Identity Federation: Allows K8s ServiceAccount in GKE to impersonate the GSA
resource "google_service_account_iam_member" "workload_identity_user" {
  service_account_id = google_service_account.portfolio_agent.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[${var.k8s_namespace}/${var.k8s_service_account}]"
}

# 3. Secret Manager Secret for Gemini API Key (Hardened secrets management)
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = {
    managed_by  = "terraform"
    application = "warrenmac-portfolio"
  }
}

# Allow the GSA to read the Gemini API key secret
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.portfolio_agent.email}"
  project   = var.project_id
}

