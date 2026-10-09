provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Generate random suffix for globally-unique bucket names if not explicitly specified
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  bucket_name = var.resume_bucket_name != "" ? var.resume_bucket_name : "warrenmac-resume-${var.project_id}-${random_id.bucket_suffix.hex}"
}

# =============================================================================
# 1. Google Cloud Services / APIs Activation
# =============================================================================
resource "google_project_service" "required_services" {
  for_each = toset([
    "container.googleapis.com",      # Google Kubernetes Engine
    "compute.googleapis.com",        # Compute Engine & Networking
    "storage.googleapis.com",        # Cloud Storage
    "iam.googleapis.com",            # Identity and Access Management
    "secretmanager.googleapis.com",  # Google Secret Manager
    "aiplatform.googleapis.com",     # Vertex AI / Gemini API
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# =============================================================================
# 2. Hardened Networking (VPC, Subnets, Cloud NAT)
# =============================================================================
module "vpc" {
  source = "./modules/vpc"

  project_id   = var.project_id
  region       = var.region
  network_name = var.network_name

  depends_on = [google_project_service.required_services]
}

# =============================================================================
# 3. Google Kubernetes Engine (GKE) Cluster
# =============================================================================
module "gke" {
  source = "./modules/gke"

  project_id          = var.project_id
  region              = var.region
  cluster_name        = var.cluster_name
  network             = module.vpc.network_name
  subnetwork          = module.vpc.subnet_name
  pods_range_name     = module.vpc.pods_range_name
  services_range_name = module.vpc.services_range_name
  enable_autopilot    = var.enable_autopilot

  depends_on = [
    google_project_service.required_services,
    module.vpc
  ]
}

# =============================================================================
# 4. Resume Storage (GCS Bucket)
# =============================================================================
module "storage" {
  source = "./modules/storage"

  project_id  = var.project_id
  region      = var.region
  bucket_name = local.bucket_name

  depends_on = [google_project_service.required_services]
}

# =============================================================================
# 5. IAM & Workload Identity Federation
# =============================================================================
module "iam" {
  source = "./modules/iam"

  project_id          = var.project_id
  resume_bucket_name  = module.storage.bucket_name
  k8s_namespace       = var.k8s_namespace
  k8s_service_account = var.k8s_service_account

  depends_on = [
    google_project_service.required_services,
    module.storage,
    module.gke
  ]
}
