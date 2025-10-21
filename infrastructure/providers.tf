terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    bucket = "262765d5d2e648c0-terraform-remote-backend"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
    infisical = {
      source  = "infisical/infisical"
      version = ">= 0.5.0"
    }
  }
}

# Configure the Google Cloud provider
# Assumes you are authenticated via gcloud CLI or a service account
provider "google" {
  project = var.project_id
  region  = var.region
}

# Configure the Infisical provider
# Assumes INFISICAL_HOST and auth informaiton is set as environment variables
# by Infisical CLI.
provider "infisical" {}
