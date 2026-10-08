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
   * Both the interactive AI chatbot and the downloadable static PDF (`/warren-mcdonald-resume.pdf`) are updated immediately without restarting pods.

2. **Ingestion Security & Indirect Prompt Injection Defense (OWASP LLM01):**
   * Verifies `%PDF-` magic bytes and rejects files > 10MB (preventing decompression bombs).
   * Scans extracted text for hidden prompt injection attacks (e.g. embedded `[SYSTEM OVERRIDE]` instructions inside uploaded resumes).

3. **In-Flight Guardrails & Canary Defense:**
   * **Ingress Guardrail:** Regex and heuristic inspection intercepts adversarial jailbreaks (`"ignore all instructions"`, roleplay escapes) before calling the LLM.
   * **Canary Token Monitoring:** Injects a dynamic cryptographic canary token into system instructions; egress scanner intercepts any response attempting to leak the prompt.
   * **Denial of Wallet Protection:** In-memory sliding window client IP rate-limiter prevents abuse.

4. **Kubernetes Hardening (Restricted Pod Security Standard):**
   * Non-root execution (`UID 10001:10001`).
   * Immutable root filesystem (`readOnlyRootFilesystem: true`).
   * All Linux capabilities dropped (`drop: ["ALL"]`).
   * Zero-Trust `NetworkPolicy` restricting egress strictly to DNS (`53`) and Google APIs (`443`).

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

### 4. Updating Your Resume in Production
Whenever you get a new job or earn a new certification:
```bash
# 1. Upload new PDF to your GCS bucket
gcloud storage cp new-resume.pdf gs://warrenmac-resume-storage/resume.pdf

# 2. (Optional) Force immediate sync without waiting for the 30s background poll:
curl -X POST https://warrenmac.com/api/internal/sync-resume
```
The agent and website will instantly reflect your new career achievements with **zero downtime and zero redeployment**.

