"""
Warren Mac - Fortified AI Resume Platform
FastAPI Service with Security Telemetry & AI Guardrail Pipeline
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from guardrails import validate_input, telemetry
from gemini_client import query_gemini
from resume_loader import sync_resume_now, get_current_resume, STORAGE_BACKEND

async def periodic_resume_watcher():
    """Background task checking storage for resume updates every 30 seconds."""
    while True:
        try:
            await asyncio.sleep(30)
            sync_resume_now()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in background resume watcher: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initial sync on pod startup
    print("Executing initial resume sync from storage...")
    sync_resume_now()
    # Launch background watcher
    watcher_task = asyncio.create_task(periodic_resume_watcher())
    yield
    # Cleanup
    watcher_task.cancel()

app = FastAPI(
    title="Warren Mac - AI DevSecOps Portfolio",
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

@app.post("/api/internal/sync-resume")
async def trigger_resume_sync():
    """
    On-demand sync endpoint for GCS Object Finalize webhooks or manual triggers.
    Enables zero-downtime hot reloading without waiting for the polling interval.
    """
    updated, message = sync_resume_now()
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
    # Extract client IP (handling reverse proxies / load balancers)
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
        or "127.0.0.1"
    )

    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Ingress Guardrail Check
    is_valid, rejection_reason = validate_input(user_message, client_ip)
    if not is_valid:
        return ChatResponse(
            response=rejection_reason,
            status="blocked",
            reason=rejection_reason
        )

    # Process via Hardened Gemini Client
    ai_response = await query_gemini(user_message)
    return ChatResponse(
        response=ai_response,
        status="ok",
        reason=""
    )

# Mount frontend static assets if available
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

