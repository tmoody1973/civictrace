variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "owner" {
  type    = string
  default = "tarik"
}

variable "image" {
  description = "Full image URI (Artifact Registry) for both services."
  type        = string
}

variable "api_service_account_email" {
  type = string
}

variable "worker_service_account_email" {
  type = string
}

variable "bearer_secret_id" {
  type = string
}

variable "max_instances" {
  description = "Finite cap required by .claude/rules/gcp-operations.md."
  type        = number
  default     = 2
}

variable "watcher_schedule" {
  description = "Cron for the source watcher (MOO-721). A few read-only API calls per run."
  type        = string
  default     = "0 6,12,18 * * *" # three checks a day is plenty for a city record
}

variable "watcher_paused" {
  description = "Pause the source watcher schedule (teardown sets this true)."
  type        = bool
  default     = false
}
