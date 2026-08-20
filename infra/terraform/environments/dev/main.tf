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

output "baseline" {
  value = module.baseline
}
