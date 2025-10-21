variable "project_id" {
  description = "The Google Cloud Project ID."
  type        = string
}

variable "region" {
  description = "The region to deploy resources in."
  type        = string
  default     = "us-east4"  # Ashburn, VA, USA
}

# --- Infisical Variables ---

variable "infisical_workspace_id" {
  description = "The Infisical Workspace (Project) ID."
  type        = string
}

variable "infisical_environment" {
  description = "The Infisical environment to save secrets to (e.g., 'dev', 'prod')."
  type        = string
  default     = "dev"
}

variable "infisical_secret_path" {
  description = "The path within Infisical to save the secrets."
  type        = string
  default     = "/gcloud/projects/family-services-475820"
}

variable "infisical_client_id_secret_name" {
  description = "The secret name in Infisical for the GCP OAuth Client ID."
  type        = string
  default     = "OAUTH_CLIENT_ID"
}

variable "infisical_client_secret_secret_name" {
  description = "The secret name in Infisical for the GCP OAuth Client Secret."
  type        = string
  default     = "OAUTH_CLIENT_SECRET_JSON"
}
