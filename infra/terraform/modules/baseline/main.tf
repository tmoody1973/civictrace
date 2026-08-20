# CivicTrace baseline (Slice 5.1, MOO-707): everything below the services.
# Buckets, Firestore, service accounts, and the bearer-token secret SHELL.
# The secret VALUE is set by a human with `gcloud secrets versions add` — never here.
# The $10 budget from MOO-690 is a documented manual exception (created before IaC existed);
# infra/scripts/verify-guardrails.sh checks it exists.

locals {
  labels = {
    app         = "civictrace"
    environment = var.environment
    owner       = var.owner
    managed-by  = "terraform"
    teardown    = "required"
  }

  # Enabled now so later slices plan cleanly; enabling an API costs nothing.
  services = [
    "run.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtasks.googleapis.com",
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
  ]
}

resource "google_project_service" "required" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# --- Raw-source vault: immutable, versioned, never public, never auto-deleted -----

resource "google_storage_bucket" "vault" {
  project                     = var.project_id
  name                        = "${var.project_id}-civictrace-vault"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  labels                      = merge(local.labels, { teardown = "retain" })

  versioning {
    enabled = true
  }
  # No delete lifecycle on purpose: raw public artifacts are the evidence spine.
  # Teardown of the vault is a human decision recorded in the teardown runbook.

  depends_on = [google_project_service.required]
}

# --- Generated packets: disposable drafts, auto-deleted --------------------------

resource "google_storage_bucket" "packets" {
  project                     = var.project_id
  name                        = "${var.project_id}-civictrace-packets"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  labels                      = local.labels

  lifecycle_rule {
    condition {
      age = var.packet_retention_days
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.required]
}

# --- Firestore: the durable ledger ----------------------------------------------
# MOO-708's only query is a single-field order_by(seq) on the ledger_events subcollection,
# served by Firestore's automatic index — no composite index is required or defined.

resource "google_firestore_database" "ledger" {
  project         = var.project_id
  name            = "(default)"
  location_id     = var.region
  type            = "FIRESTORE_NATIVE"
  deletion_policy = "DELETE"

  depends_on = [google_project_service.required]
}

# --- Service accounts: least privilege, no Owner/Editor anywhere -----------------

resource "google_service_account" "api" {
  project      = var.project_id
  account_id   = "civictrace-api"
  display_name = "CivicTrace API (Cloud Run)"
}

resource "google_service_account" "worker" {
  project      = var.project_id
  account_id   = "civictrace-worker"
  display_name = "CivicTrace worker (Cloud Tasks target)"
}

resource "google_service_account" "deploy" {
  project      = var.project_id
  account_id   = "civictrace-deploy"
  display_name = "CivicTrace deploy identity (CI/local deploys)"
}

# Worker: writes the ledger, writes/reads the vault, calls Vertex.
resource "google_project_iam_member" "worker_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = google_service_account.worker.member
}

resource "google_project_iam_member" "worker_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = google_service_account.worker.member
}

resource "google_storage_bucket_iam_member" "worker_vault_write" {
  bucket = google_storage_bucket.vault.name
  role   = "roles/storage.objectCreator"
  member = google_service_account.worker.member
}

resource "google_storage_bucket_iam_member" "worker_vault_read" {
  bucket = google_storage_bucket.vault.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.worker.member
}

# API: reads/writes the ledger (approval events), renders packets, reads the vault
# to serve exact bytes, reads the bearer secret. No Vertex access on purpose —
# the browser-facing service can never reach a model.
resource "google_project_iam_member" "api_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = google_service_account.api.member
}

resource "google_storage_bucket_iam_member" "api_vault_read" {
  bucket = google_storage_bucket.vault.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.api.member
}

resource "google_storage_bucket_iam_member" "api_packets_write" {
  bucket = google_storage_bucket.packets.name
  role   = "roles/storage.objectCreator"
  member = google_service_account.api.member
}

resource "google_storage_bucket_iam_member" "api_packets_read" {
  bucket = google_storage_bucket.packets.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.api.member
}

# --- Image registry: exists before any image push (MOO-709) ----------------------

resource "google_artifact_registry_repository" "images" {
  project       = var.project_id
  location      = var.region
  repository_id = "civictrace"
  format        = "DOCKER"
  labels        = local.labels

  depends_on = [google_project_service.required]
}

# --- Bearer secret shell: value set out-of-band by the owner ---------------------

resource "google_secret_manager_secret" "api_bearer" {
  project   = var.project_id
  secret_id = "civictrace-api-bearer"
  labels    = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "api_bearer_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.api_bearer.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.api.member
}
