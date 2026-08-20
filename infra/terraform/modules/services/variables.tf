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
