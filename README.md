# Fortified AI Resume Platform (`warrenmac.com`)

An enterprise-grade, cloud-native AI DevSecOps portfolio running on Kubernetes (OrbStack locally, Google Kubernetes Engine in production) with defense-in-depth LLM guardrails, dynamic Cloud Storage resume ingestion, and zero-downtime hot reloading.

---

## Architecture Overview

```
                          ┌─────────────────────────────────────┐
                          │    Google Cloud Storage (GCS)       │
                          │   gs://warrenmac-resume/resume.pdf  │
                          └──────────────────┬──────────────────┘
                                             │ (Upload new resume)
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Kubernetes Pod (Restricted PSS)                       │
│                                                                             │
│   ┌─────────────────────┐   Validates PDF    ┌──────────────────────────┐   │
│   │  Background Sync /  ├───────────────────►│ Ingestion Security Gate  │   │
│   │   Webhook Trigger   │   (Magic bytes,    │ - Indirect Injection     │   │
│   └─────────────────────┘    Size < 10MB)    │ - Text Extraction (pypdf)│   │
│                                              └────────────┬─────────────┘   │
│                                                           │                 │
│                                                           ▼                 │
│   ┌─────────────────────┐   Dynamic Context  ┌──────────────────────────┐   │
│   │ Gemini Flash Lite   │◄───────────────────┤ In-Memory Context Cache  │   │
│   │ Inference Engine    │                    │ + Static Download Route  │   │
│   └──────────▲──────────┘                    └──────────────────────────┘   │
│              │                                                              │
│   ┌──────────┴──────────┐                                                   │
│   │ AI DevSecOps        │  ◄── [Ingress: Rate-limiting, Prompt Injection]   │
│   │ Dual Guardrails     │  ──► [Egress: Canary Token Check, PII Scrubber]   │
│   └─────────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key AI DevSecOps Features

1. **Zero-Redeployment Dynamic Ingestion:**
   * When a new `resume.pdf` is uploaded to Google Cloud Storage (or the local storage mount), the application detects the SHA256 change, validates and parses the document, and hot-reloads it in-memory.
   * Both the interactive AI chatbot and the downloadable PDF (`/warren-mcdonald-resume.pdf`, served from memory so the container filesystem can stay read-only) are updated immediately without restarting pods.

2. **Ingestion Security & Indirect Prompt Injection Defense (OWASP LLM01):**
   * Verifies `%PDF-` magic bytes and rejects files > 10MB (preventing decompression bombs).
   * Scans extracted text for hidden prompt injection attacks (e.g. embedded `[SYSTEM OVERRIDE]` instructions inside uploaded resumes).

3. **In-Flight Guardrails & Canary Defense:**
   * **Ingress Guardrail:** Regex and heuristic inspection intercepts adversarial jailbreaks (`"ignore all instructions"`, roleplay escapes) before calling the LLM.
   * **Canary Token Monitoring:** Injects a dynamic cryptographic canary token into system instructions; egress scanner intercepts any response attempting to leak the prompt.
   * **Denial of Wallet Protection:** In-memory sliding window client IP rate-limiter prevents abuse. Client IPs are resolved from only the load balancer's trusted `X-Forwarded-For` hops (`XFF_TRUSTED_HOPS`), so a spoofed header can't dodge the limit.

4. **Kubernetes Hardening (Restricted Pod Security Standard):**
   * Non-root execution (`UID 10001:10001`).
   * Immutable root filesystem (`readOnlyRootFilesystem: true`).
   * All Linux capabilities dropped (`drop: ["ALL"]`).
   * Zero-Trust `NetworkPolicy` restricting egress strictly to DNS (`53`) and Google APIs (`443`).

5. **HTTP & API Hardening:**
   * Strict Content-Security-Policy with no `'unsafe-inline'`, plus HSTS, `X-Frame-Options: DENY`, `nosniff`, Referrer-Policy and Permissions-Policy on every response.
   * Same-origin only: no CORS headers are issued, and interactive API docs are disabled in production.
   * Internal endpoints require a bearer token (constant-time compare) and fail closed when unconfigured; the optional password gate has no default and is brute-force rate limited.

6. **Software Supply Chain:**
   * Every GitHub Action pinned to a full commit SHA; base images pinned by digest; Dependabot keeps both current.
   * Blocking Trivy gates on secrets, dependencies, Kubernetes manifests and the built image (fixable HIGH/CRITICAL).
   * Production deploys the exact image digest that was signed, after `cosign verify` checks it came from this repo's `main` pipeline.

---

## Frontend Development

The site is a single static page (`app/frontend/index.html` + `app.js`) styled with **Tailwind CSS v4**. `app/frontend/styles.css` is a build artifact: the Docker image compiles it from `app/frontend/src/input.css` using the pinned, checksum-verified Tailwind standalone CLI (no Node.js required). It is git-ignored.

For local development, install the CLI (`brew install tailwindcss` or download a [standalone binary](https://github.com/tailwindlabs/tailwindcss/releases)) and run it in watch mode alongside uvicorn:

```bash
tailwindcss -i app/frontend/src/input.css -o app/frontend/styles.css --watch
```

Photos (headshot, project screenshots, hero background, logos) live in `app/frontend/images/`. See [`app/frontend/images/README.md`](app/frontend/images/README.md) for the expected filenames and sizes. Missing images fall back to placeholders automatically.

---

## Production Deployment (GCP GKE + Cloud Storage)

### 1. GCS Bucket Setup
Create a dedicated private GCS bucket for your resume:
```bash
gcloud storage buckets create gs://warrenmac-resume-storage \
  --location=us-central1 \
  --uniform-bucket-level-access
```

Upload your resume:
```bash
gcloud storage cp my-new-resume.pdf gs://warrenmac-resume-storage/resume.pdf
```

### 2. Workload Identity Federation (Zero-Secret Access)
Allow the GKE Kubernetes Service Account (`KSA`) to read from the GCS bucket without hardcoding service account JSON keys:

```bash
# 1. Create GCP Service Account
gcloud iam service-accounts create portfolio-agent-sa \
  --display-name="Portfolio Agent Storage Reader"

# 2. Grant Storage Object Viewer role
gcloud storage buckets add-iam-policy-binding gs://warrenmac-resume-storage \
  --member="serviceAccount:portfolio-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# 3. Bind to GKE Kubernetes Service Account
gcloud iam service-accounts add-iam-policy-binding \
  portfolio-agent-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:${PROJECT_ID}.svc.id.goog[portfolio/portfolio-agent]"
```

### 3. Environment Variables in Kubernetes
In `k8s/portfolio.yaml`:
```yaml
env:
  - name: STORAGE_BACKEND
    value: "gcs"
  - name: GCS_BUCKET_NAME
    value: "warrenmac-resume-storage"
  - name: GCS_OBJECT_NAME
    value: "resume.pdf"
```

### 4. Continuous Deployment via GitHub Actions (Zero-Secret WIF)
Code changes merged to `main` trigger the automated CI/CD pipeline in `.github/workflows/ci-cd.yaml`:
1. **Adversarial & Functional Tests**: Runs Pytest across LLM guardrails, API routes, and loaders.
2. **Security & IaC Audits**: Trivy secret detection (blocking gate) and dependency vulnerability scan.
3. **Container Build, Scan & Attestation**: Multi-stage build pushed to GHCR, scanned by Trivy (blocking on fixable HIGH/CRITICAL), and signed keylessly with **Sigstore Cosign**.
4. **Automated GKE Continuous Deployment**: GitHub Actions authenticates keylessly via **Google Cloud Workload Identity Federation**, runs `cosign verify` on the signed digest, renders it into the manifest (`ghcr.io/wmickeyd/warrenmac-portfolio@sha256:<digest>`), applies once, and verifies zero-downtime rollout with `kubectl rollout status`.

> `k8s/portfolio.yaml` holds a digest placeholder that CI rewrites, so it is not meant to be applied by hand.

### 5. Infrastructure as Code Automation (Terraform GitOps)
Changes to infrastructure in `terraform/` trigger `.github/workflows/terraform.yaml`:
* **Pull Requests**: Trivy IaC audit, `terraform fmt -check`, `terraform init`, and `terraform plan`, automatically posting the formatted plan summary as a comment on the PR.
* **Push to `main`**: Runs `terraform apply -auto-approve` using keyless Workload Identity Federation.

### 6. Updating Your Resume in Production (Hot-Reload)
Whenever you get a new job or earn a new certification:
```bash
# 1. Upload new PDF to your GCS bucket
gcloud storage cp new-resume.pdf gs://warrenmac-resume-storage/resume.pdf

# 2. (Optional) Force immediate sync without waiting for the 30s background poll
#    (token from the `portfolio-app` secret; the endpoint returns 404 if no token is configured):
curl -X POST -H "Authorization: Bearer $RESUME_SYNC_TOKEN" https://warrenmac.com/api/internal/sync-resume
```
The agent and website will instantly reflect your new career achievements with **zero downtime and zero redeployment**.

