# GMail push notifications
#
# This Terraform configuration sets up the necessary Google Cloud resources
# to enable GMail push notifications via Pub/Sub, and saves OAuth credentials
# to Infisical for secure management.

# --- Variables ---

variable "oauth_gmail_app_name" {
  description = "The display name for the OAuth GMail application."
  type        = string
  default     = "Family Services GMail Reader"
}

variable "topic_name" {
  description = "The name for the Pub/Sub topic."
  type        = string
  default     = "gmail-push-notifications"
}

# --- Resources ---

# Enable API for GMail
resource "google_project_service" "gmail_api" {
  project = var.project_id
  service = "gmail.googleapis.com"
  disable_on_destroy = false
}

# Enable API for Pub/Sub
resource "google_project_service" "pubsub_api" {
  project = var.project_id
  service = "pubsub.googleapis.com"
  disable_on_destroy = false
}

# Enable API for Google Identity Platform
resource "google_project_service" "identity_platform_api" {
  project = var.project_id
  service = "identitytoolkit.googleapis.com"
  disable_on_destroy = false
}

resource "google_pubsub_topic" "gmail_push" {
  project = var.project_id
  name    = var.topic_name

  depends_on = [
    google_project_service.pubsub_api
  ]
}

resource "google_pubsub_topic_iam_member" "gmail_push_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.gmail_push.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:gmail-api-push@system.gserviceaccount.com"
}
