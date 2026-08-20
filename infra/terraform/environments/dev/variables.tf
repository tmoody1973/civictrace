variable "project_id" {
  description = "Dev project id (human-owned, MOO-690)."
  type        = string
  default     = "civictrace-dev-tm"
}

variable "region" {
  description = "Single region for all regional resources."
  type        = string
  default     = "us-central1"
}
