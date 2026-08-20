variable "project_id" {
  description = "Target GCP project (human-owned; created in MOO-690)."
  type        = string
}

variable "region" {
  description = "Single region for Firestore, GCS, and (later) Cloud Run and BigQuery."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment label value (dev or demo)."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner label value."
  type        = string
  default     = "tarik"
}

variable "packet_retention_days" {
  description = "Generated DRAFT packets are disposable; deleted automatically after this many days."
  type        = number
  default     = 30
}
