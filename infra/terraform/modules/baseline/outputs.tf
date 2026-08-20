output "vault_bucket" {
  value = google_storage_bucket.vault.name
}

output "packets_bucket" {
  value = google_storage_bucket.packets.name
}

output "api_service_account_email" {
  value = google_service_account.api.email
}

output "worker_service_account_email" {
  value = google_service_account.worker.email
}

output "deploy_service_account_email" {
  value = google_service_account.deploy.email
}

output "bearer_secret_id" {
  value = google_secret_manager_secret.api_bearer.secret_id
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}
