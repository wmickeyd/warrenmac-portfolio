"""
Warren Mac - Fortified AI Resume Platform
FastAPI Service with Security Telemetry & AI Guardrail Pipeline
"""

import os
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from guardrails import validate_input, telemetry
import contact
from gemini_client import GEMINI_MODEL, query_gemini
from resume_loader import sync_resume_now, get_current_resume, STORAGE_BACKEND
from mlflow_client import init_mlflow, log_chat_trace, log_resume_sync_event
from prometheus_fastapi_instrumentator import Instrumentator
from metrics import (
    CONTACT_SUBMISSIONS_TOTAL,
    LLM_INFERENCE_DURATION_SECONDS,
    LLM_QUERIES_TOTAL,
    RESUME_CHARACTERS,
    RESUME_SYNC_TOTAL,
)

async def periodic_resume_watcher():
    """Background task checking storage for resume updates every 30 seconds."""
    while True:
        try:
            await asyncio.sleep(30)
            updated, _ = sync_resume_now()
            RESUME_CHARACTERS.set(len(get_current_resume()))
            if updated:
                RESUME_SYNC_TOTAL.labels(status="updated").inc()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in background resume watcher: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MLflow tracking if configured
    init_mlflow()
    # Initial sync on pod startup
    print("Executing initial resume sync from storage...")
    updated, _ = sync_resume_now()
    RESUME_CHARACTERS.set(len(get_current_resume()))
    RESUME_SYNC_TOTAL.labels(status="updated" if updated else "initial").inc()
    # Launch background watcher
    watcher_task = asyncio.create_task(periodic_resume_watcher())
    yield
    # Cleanup
    watcher_task.cancel()

app = FastAPI(
    title="Warren McDonald - AI DevSecOps Portfolio",
    description="Fortified AI Resume Agent on Kubernetes with OWASP LLM Guardrails",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def protect_metrics_endpoint(request: Request, call_next):
    """Restricts /metrics to internal cluster traffic when running in production."""
    if request.url.path == "/metrics":
        if os.getenv("STORAGE_BACKEND") == "gcs" or os.getenv("ENVIRONMENT") == "production":
            if request.headers.get("x-forwarded-for"):
                return Response(status_code=403, content="Forbidden: Internal metrics endpoint only")
    return await call_next(request)

# Prometheus Metrics Instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

@app.post("/api/internal/sync-resume")
async def trigger_resume_sync():
    """
    On-demand sync endpoint for GCS Object Finalize webhooks or manual triggers.
    Enables zero-downtime hot reloading without waiting for the polling interval.
    """
    updated, message = sync_resume_now()
    RESUME_CHARACTERS.set(len(get_current_resume()))
    RESUME_SYNC_TOTAL.labels(status="updated" if updated else "unchanged").inc()
    return {
        "updated": updated,
        "message": message,
        "storage_backend": STORAGE_BACKEND
    }

@app.get("/api/resume-status")
async def get_resume_status():
    """Returns metadata about the currently ingested resume."""
    return {
        "storage_backend": STORAGE_BACKEND,
        "active_length_chars": len(get_current_resume()),
        "preview": get_current_resume()[:300] + "..."
    }

# Password Gate Configuration (Feature Flag: disabled by default)
ENABLE_PASSWORD_GATE = os.getenv("ENABLE_PASSWORD_GATE", "false").lower() == "true"
SITE_ACCESS_PASSWORD = os.getenv("SITE_ACCESS_PASSWORD", "devsecops2026")

class AuthVerifyRequest(BaseModel):
    password: str

@app.get("/api/auth/status")
async def get_auth_status():
    """Returns whether the password barrier is currently enabled."""
    return {"enabled": ENABLE_PASSWORD_GATE}

@app.post("/api/auth/verify")
async def verify_password(payload: AuthVerifyRequest):
    """Verifies the passcode against the configured access password."""
    if not ENABLE_PASSWORD_GATE:
        return {"success": True, "message": "Gate disabled"}
    if payload.password == SITE_ACCESS_PASSWORD:
        return {"success": True, "message": "Access granted"}
    return {"success": False, "message": "Invalid access code. Please try again."}

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000, description="User question or prompt")

class ChatResponse(BaseModel):
    response: str
    status: str  # "ok" or "blocked"
    reason: str = ""

@app.get("/health")
async def health_check():
    """Kubernetes liveness and readiness probe endpoint."""
    return {"status": "healthy", "service": "warrenmac-portfolio-agent"}

@app.get("/api/security-stats")
async def get_security_stats():
    """Live DevSecOps telemetry for the public dashboard."""
    return telemetry.get_stats()

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, payload: ChatRequest):
    start_time = time.perf_counter()

    # Extract client IP (handling reverse proxies / load balancers)
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
        or "127.0.0.1"
    )

    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    model_name = GEMINI_MODEL

    # Ingress Guardrail Check
    is_valid, rejection_reason = validate_input(user_message, client_ip)
    if not is_valid:
        latency_ms = (time.perf_counter() - start_time) * 1000
        LLM_QUERIES_TOTAL.labels(status="blocked", model=model_name).inc()
        log_chat_trace(
            user_prompt=user_message,
            ai_response=rejection_reason,
            status="blocked",
            client_ip=client_ip,
            latency_ms=latency_ms,
            guardrail_reason=rejection_reason
        )
        return ChatResponse(
            response=rejection_reason,
            status="blocked",
            reason=rejection_reason
        )

    # Process via Hardened Gemini Client
    llm_start = time.perf_counter()
    try:
        ai_response = await query_gemini(user_message)
        llm_duration = time.perf_counter() - llm_start
        LLM_INFERENCE_DURATION_SECONDS.observe(llm_duration)
        LLM_QUERIES_TOTAL.labels(status="ok", model=model_name).inc()
    except Exception as e:
        llm_duration = time.perf_counter() - llm_start
        LLM_INFERENCE_DURATION_SECONDS.observe(llm_duration)
        LLM_QUERIES_TOTAL.labels(status="error", model=model_name).inc()
        raise e

    latency_ms = (time.perf_counter() - start_time) * 1000
    log_chat_trace(
        user_prompt=user_message,
        ai_response=ai_response,
        status="ok",
        client_ip=client_ip,
        latency_ms=latency_ms,
        guardrail_reason=""
    )
    return ChatResponse(
        response=ai_response,
        status="ok",
        reason=""
    )

class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    company: str = Field("", max_length=120)
    message: str = Field(..., min_length=10, max_length=5000)
    website: str = Field("", max_length=200)  # Honeypot: hidden from humans, bots fill it in

@app.post("/api/contact")
async def contact_endpoint(request: Request, payload: ContactRequest):
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
        or "127.0.0.1"
    )

    # Silently accept bot submissions so they don't learn to skip the honeypot
    if payload.website:
        CONTACT_SUBMISSIONS_TOTAL.labels(status="spam").inc()
        telemetry.record_event("CONTACT_SPAM", f"Honeypot triggered from IP {client_ip}")
        return {"success": True}

    if not contact.contact_rate_limiter.is_allowed(client_ip):
        CONTACT_SUBMISSIONS_TOTAL.labels(status="rate_limited").inc()
        telemetry.record_event("RATE_LIMIT", f"IP {client_ip} exceeded contact form limit")
        raise HTTPException(status_code=429, detail="Too many messages. Please try again later or reach out on LinkedIn.")

    if not contact.is_configured():
        CONTACT_SUBMISSIONS_TOTAL.labels(status="unconfigured").inc()
        raise HTTPException(status_code=503, detail="Contact form is temporarily unavailable. Please reach out on LinkedIn.")

    sent = await contact.send_contact_email(
        name=payload.name.strip(),
        email=payload.email.strip(),
        company=payload.company.strip(),
        message=payload.message.strip(),
    )
    if not sent:
        CONTACT_SUBMISSIONS_TOTAL.labels(status="error").inc()
        raise HTTPException(status_code=502, detail="Your message couldn't be delivered. Please try again or reach out on LinkedIn.")

    CONTACT_SUBMISSIONS_TOTAL.labels(status="sent").inc()
    return {"success": True}

# Mount frontend static assets if available
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

