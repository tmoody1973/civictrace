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

variable "deploy_services" {
  description = "Create Cloud Run services + queue + topic (needs a pushed image and a bearer secret version)."
  type        = bool
  default     = false
}

variable "image" {
  description = "Full image URI for both Cloud Run services."
  type        = string
  default     = ""
}
