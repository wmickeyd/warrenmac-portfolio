output "bucket_name" {
  description = "The name of the resume GCS bucket"
  value       = google_storage_bucket.resume_bucket.name
}

output "bucket_url" {
  description = "The gsutil URL for the resume GCS bucket"
  value       = google_storage_bucket.resume_bucket.url
}
