terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "project-60b1ce90-88cb-4ae2-8b4-tfstate"
    prefix = "portfolio/production"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

