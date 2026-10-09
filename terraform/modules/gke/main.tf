# Production-hardened Google Kubernetes Engine (GKE) Cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  project  = var.project_id
  location = var.region

  network    = var.network
  subnetwork = var.subnetwork

  # GKE Autopilot provides Google-managed hardening, automated CIS compliance, and Restricted PSS enforcement
  enable_autopilot    = var.enable_autopilot
  deletion_protection = var.deletion_protection

  # VPC-native routing configuration
  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Private Cluster Configuration:
  # - Worker nodes have NO public IP addresses (isolated behind Cloud NAT)
  # - Control plane has a public endpoint for authorized admin kubectl access
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  # Workload Identity: Links Kubernetes ServiceAccounts to Google Cloud IAM
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  release_channel {
    channel = "REGULAR"
  }

  # Shielded Nodes and Security Posture
  security_posture_config {
    mode               = "BASIC"
    vulnerability_mode = "VULNERABILITY_BASIC"
  }

  # Maintenance Window: Sunday 02:00 - 06:00 UTC
  maintenance_policy {
    recurring_window {
      start_time = "2026-01-01T02:00:00Z"
      end_time   = "2026-01-01T06:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SU"
    }
  }

  lifecycle {
    ignore_changes = [
      # Autopilot adjusts some fields dynamically
      initial_node_count
    ]
  }
}
