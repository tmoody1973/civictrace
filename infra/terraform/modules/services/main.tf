# CivicTrace services (Slice 5.3, MOO-709): two Cloud Run services, one queue, one topic.
# Worker: IAM-only invocation (Tasks + Pub/Sub push, both as the worker SA). Never allUsers.
# API: public URL; the bearer gate lives in the app, fed from Secret Manager.
# Both: min 0, finite max — the guardrail script enforces this shape before every deploy.

locals {
  labels = {
    app         = "civictrace"
    environment = var.environment
    owner       = var.owner
    managed-by  = "terraform"
    teardown    = "required"
  }
  queue_name = "civictrace-ingest"
  # Cloud Run deterministic URL: no cycle between the worker service and its own env.
  worker_url = "https://civictrace-worker-${data.google_project.this.number}.${var.region}.run.app"
}

data "google_project" "this" {
  project_id = var.project_id
}

# --- Worker: IAM-only Cloud Tasks target -----------------------------------------

resource "google_cloud_run_v2_service" "worker" {
  project             = var.project_id
  name                = "civictrace-worker"
  location            = var.region
  labels              = local.labels
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL" # authentication is IAM, not network: no allUsers binding exists

  template {
    service_account = var.worker_service_account_email
    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }
    containers {
      image = var.image
      resources {
        limits            = { cpu = "1", memory = "1Gi" }
        startup_cpu_boost = true
      }
      startup_probe {
        tcp_socket {
          port = 8080
        }
        period_seconds    = 10
        failure_threshold = 30
      }
      env {
        name  = "CIVICTRACE_APP"
        value = "app.worker:app"
      }
      env {
        name  = "CIVICTRACE_WORKER"
        value = "1"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "CIVICTRACE_REGION"
        value = var.region
      }
      env {
        name  = "CIVICTRACE_TASKS_QUEUE"
        value = local.queue_name
      }
      env {
        name  = "CIVICTRACE_WORKER_URL"
        value = local.worker_url
      }
      env {
        name  = "CIVICTRACE_WORKER_SA"
        value = var.worker_service_account_email
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = "global" # Gemini 3.x Flash is served only from the global Vertex location
      }
      env {
        # Worker-only (MOO-710): each event needs a corpus_artifacts row in BigQuery.
        name  = "CIVICTRACE_BQ_PREFILTER"
        value = "1"
      }
      env {
        # Live Gemini Flash for the full agent chain (extraction, delta, review,
        # inquiry). "fake" remains the local/CI default; only the worker runs live.
        name  = "CIVICTRACE_RUNNER"
        value = "adk"
      }
      env {
        # The vault retrieves canonical bytes from the City's allowlisted servers
        # at ingest, hash-verified against the reviewed manifest (MOO-714).
        name  = "CIVICTRACE_LIVE_FETCH"
        value = "1"
      }
      env {
        name  = "CIVICTRACE_BQ_DATASET"
        value = "civictrace_dev"
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "worker_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.worker_service_account_email}"
}

# The worker enqueues tasks and mints OIDC tokens as itself.
resource "google_project_iam_member" "worker_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${var.worker_service_account_email}"
}

resource "google_service_account_iam_member" "worker_acts_as_self" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.worker_service_account_email}"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.worker_service_account_email}"
}

# Pub/Sub's service agent must be able to mint the worker-SA OIDC token for push auth.
resource "google_service_account_iam_member" "pubsub_token_creator" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.worker_service_account_email}"
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# --- API: public URL, bearer gate in the app -------------------------------------

resource "google_cloud_run_v2_service" "api" {
  project             = var.project_id
  name                = "civictrace-api"
  location            = var.region
  labels              = local.labels
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.api_service_account_email
    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }
    containers {
      image = var.image
      resources {
        limits            = { cpu = "1", memory = "1Gi" }
        startup_cpu_boost = true
      }
      startup_probe {
        tcp_socket {
          port = 8080
        }
        period_seconds    = 10
        failure_threshold = 30
      }
      env {
        name  = "CIVICTRACE_APP"
        value = "app.main:app"
      }
      env {
        name  = "CIVICTRACE_CLOUD"
        value = "1"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "CIVICTRACE_REGION"
        value = var.region
      }
      env {
        name = "CIVICTRACE_API_BEARER"
        value_source {
          secret_key_ref {
            secret  = var.bearer_secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers" # deliberate (decision 004): app-layer bearer guards every route
}

# --- Queue and topic --------------------------------------------------------------

resource "google_cloud_tasks_queue" "ingest" {
  project  = var.project_id
  location = var.region
  name     = local.queue_name

  rate_limits {
    max_concurrent_dispatches = 2
    max_dispatches_per_second = 2
  }
  retry_config {
    max_attempts = 3
  }
}

resource "google_pubsub_topic" "source_events" {
  project = var.project_id
  name    = "civictrace-source-events"
  labels  = local.labels
}

resource "google_pubsub_subscription" "source_events_push" {
  project = var.project_id
  name    = "civictrace-source-events-push"
  topic   = google_pubsub_topic.source_events.id
  labels  = local.labels

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.worker.uri}/pubsub/source-events"
    oidc_token {
      service_account_email = var.worker_service_account_email
    }
  }
  ack_deadline_seconds = 60
  expiration_policy {
    ttl = "" # never expires on its own; teardown removes it deliberately
  }
}

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "worker_url" {
  value = google_cloud_run_v2_service.worker.uri
}

output "topic" {
  value = google_pubsub_topic.source_events.id
}

