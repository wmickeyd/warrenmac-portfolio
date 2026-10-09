# Google Cloud Infrastructure via Terraform

This directory contains modular, production-hardened Terraform configurations for **The Fortified AI Resume Platform** on Google Cloud Platform (GCP).

---

## Architecture Overview

```
                                      Internet
                                         │
                                   [ Cloud NAT ]
                                         │
┌────────────────────────── Portfolio Custom VPC ──────────────────────────┐
│                                                                          │
│  ┌─────────────────────── GKE Autopilot Cluster ──────────────────────┐  │
│  │                                                                    │  │
│  │  Namespace: portfolio (Restricted Pod Security Standard)           │  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  Pod: portfolio-agent                                        │  │  │
│  │  │  • K8s ServiceAccount: portfolio-agent                        │  │  │
│  │  │  • Least-Privilege UID 10001, ReadOnlyRootFS, No Priv Esc     │  │  │
│  │  └──────────────┬───────────────────────────────┬───────────────┘  │  │
│  └─────────────────┼───────────────────────────────┼──────────────────┘  │
└────────────────────┼───────────────────────────────┼─────────────────────┘
                     │ Workload Identity             │ Workload Identity
                     ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐
       │   Google Cloud Storage    │   │   Google Secret Manager   │
       │   (Resume PDF Bucket)     │   │   (Gemini API Key Secret) │
       │  • Uniform Bucket Access  │   │  • Least-privilege        │
       │  • Public Prevention      │   │    Secret Accessor        │
       │  • Object Versioning      │   │                           │
       └───────────────────────────┘   └───────────────────────────┘
```

The infrastructure is split into 4 isolated modules:
* **`modules/vpc`**: Custom VPC, subnets with secondary ranges for Pods/Services, Cloud Router, Cloud NAT, and zero-trust firewall rules.
* **`modules/gke`**: Private GKE Autopilot cluster with automated hardening, CIS compliance, and Workload Identity enabled.
* **`modules/storage`**: Hardened GCS bucket for dynamic resume PDF storage with versioning, lifecycle rules, and public access prevention.
* **`modules/iam`**: Dedicated Google Service Account (`portfolio-agent-sa`), Workload Identity binding to Kubernetes, and least-privilege IAM roles.

---

## Part 1: Deploying from Your Local Machine

### 1. Prerequisites
Ensure you have the following CLI tools installed:
* **Terraform** (`>= 1.5.0`)
* **Google Cloud SDK (`gcloud`)**
* **`kubectl`**

### 2. Authenticate to Google Cloud
Log in to your GCP account and set up Application Default Credentials (ADC) for Terraform:
```bash
# 1. Authenticate gcloud CLI
gcloud auth login

# 2. Authenticate Application Default Credentials (used by Terraform Google provider)
gcloud auth application-default login

# 3. Set your active project
gcloud config set project <YOUR_GCP_PROJECT_ID>
```

### 3. Configure Input Variables
Copy the example variable template and supply your GCP project details:
```bash
cd ~/Projects/warrenmac-portfolio/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id       = "your-gcp-project-id"  # e.g., "project-60b1ce90-88cb-4ae2-8b4"
region           = "us-central1"
cluster_name     = "portfolio-cluster"
network_name     = "portfolio-vpc"
enable_autopilot = true
```

### 4. Initialize and Validate
Initialize provider plugins and modules:
```bash
terraform init
terraform validate
```

### 5. Review the Plan and Apply
Generate a speculative execution plan and provision the resources:
```bash
# Preview changes (20 resources planned)
terraform plan

# Apply changes to Google Cloud
terraform apply
```
*Note: GKE cluster creation typically takes 5–8 minutes.*

---

### 6. Post-Deployment Steps

#### A. Connect `kubectl` to GKE
Run the connection command generated in the Terraform outputs:
```bash
$(terraform output -raw kubectl_connect_command)

# Verify cluster connection
kubectl get nodes
```

#### B. Upload Your Resume PDF to GCS
Retrieve the provisioned bucket name and upload your initial resume:
```bash
BUCKET_NAME=$(terraform output -raw gcs_resume_bucket)

# Upload the authentic resume PDF to the bucket
gcloud storage cp ../app/frontend/warren-mcdonald-resume.pdf gs://${BUCKET_NAME}/resume.pdf
```

#### C. Store the Gemini API Key in Secret Manager
Populate the Secret Manager secret created by Terraform:
```bash
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
```

#### D. Deploy the Portfolio Application to GKE
1. Annotate the Kubernetes ServiceAccount with the Workload Identity GSA:
   ```bash
   GSA_EMAIL=$(terraform output -raw gsa_workload_identity_email)
   
   kubectl apply -f ../k8s/portfolio.yaml
   kubectl annotate serviceaccount portfolio-agent \
     --namespace portfolio \
     iam.gke.io/gcp-service-account=${GSA_EMAIL} \
     --overwrite
   ```

2. Update the Deployment environment variables for GCS in `k8s/portfolio.yaml`:
   ```yaml
   - name: STORAGE_BACKEND
     value: "gcs"
   - name: GCS_BUCKET_NAME
     value: "<YOUR_GCS_BUCKET_NAME>"
   - name: GCS_OBJECT_NAME
     value: "resume.pdf"
   ```

---

### 7. Destroy / Teardown
To cleanly tear down all infrastructure and prevent ongoing cloud costs:
```bash
terraform destroy
```

---

## Part 2: GitOps Infrastructure Automation via GitHub Actions

See the main documentation below for details on how to set up automated, keyless CI/CD for Terraform using **Workload Identity Federation (WIF)** and dedicated Pull Request/Apply workflows.

