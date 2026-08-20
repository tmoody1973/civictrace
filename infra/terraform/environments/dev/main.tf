# CivicTrace dev environment (Slice 5, MOO-707+).
# State: LOCAL on the owner's machine (gitignored). Deliberate for a solo hackathon —
# a remote state bucket would itself be pre-IaC infrastructure. Revisit if a second
# operator ever appears. # ponytail: local state; GCS backend when a team exists.

terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "baseline" {
  source      = "../../modules/baseline"
  project_id  = var.project_id
  region      = var.region
  environment = "dev"
  owner       = "tarik"
}

# Services deploy only when an image exists (MOO-709): plan with -var deploy_services=true
# after the image is built and pushed. The bearer secret must hold a version first.
module "services" {
  source     = "../../modules/services"
  count      = var.deploy_services ? 1 : 0
  project_id = var.project_id
  region     = var.region

  image                        = var.image
  api_service_account_email    = module.baseline.api_service_account_email
  worker_service_account_email = module.baseline.worker_service_account_email
  bearer_secret_id             = module.baseline.bearer_secret_id
}

output "baseline" {
  value = module.baseline
}

output "services" {
  value = var.deploy_services ? module.services[0] : null
}
