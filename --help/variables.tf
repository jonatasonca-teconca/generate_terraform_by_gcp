variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "--help"
}

variable "region" {
  description = "Default GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default GCP zone"
  type        = string
  default     = "us-central1-a"
}
