# Terraform infrastructure
#
# This Terraform configuration sets up backend storage of state in a GCS bucket.

resource "random_id" "tf_backend" {
  byte_length = 8
}

resource "google_storage_bucket" "tf_backend" {
  name     = "${random_id.tf_backend.hex}-terraform-remote-backend"
  location = "US"

  force_destroy               = false
  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}