output "service_account_email" {
  description = "The email of the created Google Service Account"
  value       = google_service_account.portfolio_agent.email
}

output "service_account_name" {
  description = "The fully-qualified name of the Google Service Account"
  value       = google_service_account.portfolio_agent.name
}

output "gemini_secret_id" {
  description = "Secret Manager secret ID for the Gemini API key"
  value       = google_secret_manager_secret.gemini_api_key.secret_id
}

