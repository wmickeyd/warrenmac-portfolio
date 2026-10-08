"""
Dynamic Resume Loader & Ingestion Pipeline
Supports:
1. Google Cloud Storage (GCS) in production
2. Local volume mount in development (OrbStack)
3. PDF magic bytes and size verification
4. Indirect Prompt Injection scanning on ingested text (OWASP LLM01)
5. Zero-downtime in-memory hot reloading
"""

import os
import io
import re
import hashlib
import logging
from typing import Tuple, Optional
import pypdf

from resume_data import WARREN_RESUME as FALLBACK_RESUME
from guardrails import telemetry

logger = logging.getLogger("resume_loader")
logging.basicConfig(level=logging.INFO)

# Configuration
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # "local" or "gcs"
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "warrenmac-resume-storage")
GCS_OBJECT_NAME = os.getenv("GCS_OBJECT_NAME", "resume.pdf")

# Local storage path (shared with frontend static directory)
LOCAL_RESUME_PATH = os.getenv(
    "LOCAL_RESUME_PATH",
    os.path.join(os.path.dirname(__file__), "..", "frontend", "warren-mcdonald-resume.pdf")
)

# In-memory cached state
_active_resume_text: str = FALLBACK_RESUME
_last_file_hash: str = ""

# Indirect prompt injection signatures (attacker embedding instructions into uploaded PDF)
INDIRECT_INJECTION_PATTERNS = [
    r"(?i)\[system override\]",
    r"(?i)\[admin instructions\]",
    r"(?i)ignore all (previous|prior) instructions",
    r"(?i)you are now in developer mode",
    r"(?i)forget everything above",
    r"(?i)exfiltrate.*canary",
]

def _compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _validate_and_extract_pdf(pdf_bytes: bytes) -> Tuple[bool, str]:
    """
    Validates PDF format, checks for indirect injection attacks,
    and extracts clean text content.
    """
    # 1. Size constraint check (prevent decompression / memory bombs)
    if len(pdf_bytes) > 10 * 1024 * 1024:
        return False, "File exceeds maximum allowable size (10MB)"

    # 2. Magic bytes check
    if not pdf_bytes.startswith(b"%PDF-"):
        return False, "Invalid file format: missing PDF magic bytes (%PDF-)"

    # 3. Extract text via pypdf
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            extracted_pages.append(f"--- PAGE {i+1} ---\n{text}")
        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            return False, "PDF contains no extractable text"

        # 4. Indirect Prompt Injection Scan (OWASP LLM01)
        for pattern in INDIRECT_INJECTION_PATTERNS:
            if re.search(pattern, full_text):
                telemetry.record_event(
                    "INDIRECT_INJECTION_BLOCKED",
                    f"Suspicious payload detected in uploaded resume PDF: {pattern}"
                )
                return False, f"Security Alert: Document rejected due to indirect injection pattern: {pattern}"

        return True, full_text

    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return False, f"PDF extraction error: {str(e)}"

def _fetch_from_gcs() -> Optional[bytes]:
    """Downloads PDF bytes from Google Cloud Storage using Workload Identity."""
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(GCS_OBJECT_NAME)
        if not blob.exists():
            logger.warning(f"GCS blob gs://{GCS_BUCKET_NAME}/{GCS_OBJECT_NAME} does not exist.")
            return None
        return blob.download_as_bytes()
    except Exception as e:
        logger.error(f"Error fetching from GCS: {e}")
        return None

def _fetch_from_local() -> Optional[bytes]:
    """Reads PDF bytes from local mounted file."""
    if not os.path.exists(LOCAL_RESUME_PATH):
        logger.warning(f"Local file does not exist: {LOCAL_RESUME_PATH}")
        return None
    try:
        with open(LOCAL_RESUME_PATH, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading local file: {e}")
        return None

def sync_resume_now() -> Tuple[bool, str]:
    """
    Fetches the resume from storage, verifies it, and updates the in-memory context.
    Returns (updated_or_unchanged, status_message).
    """
    global _active_resume_text, _last_file_hash

    pdf_bytes = _fetch_from_gcs() if STORAGE_BACKEND == "gcs" else _fetch_from_local()
    if not pdf_bytes:
        return False, "Could not retrieve resume from storage backend."

    new_hash = _compute_hash(pdf_bytes)
    if new_hash == _last_file_hash:
        return False, "Resume file unchanged; skipping re-parse."

    # Validate and extract text
    is_valid, result = _validate_and_extract_pdf(pdf_bytes)
    if not is_valid:
        logger.error(f"Resume validation failed: {result}")
        return False, f"Validation failed: {result}"

    # If backend is GCS, update the local static frontend copy so web downloads stay in sync
    if STORAGE_BACKEND == "gcs":
        try:
            os.makedirs(os.path.dirname(LOCAL_RESUME_PATH), exist_ok=True)
            with open(LOCAL_RESUME_PATH, "wb") as f:
                f.write(pdf_bytes)
            logger.info("Updated local static copy from GCS")
        except Exception as e:
            logger.warning(f"Could not write static copy: {e}")

    # Format into knowledge base context
    formatted_resume = f"""# Warren David McDonald - AI DevSecOps Engineer

**Domain:** https://warrenmac.com
**LinkedIn:** https://www.linkedin.com/in/warren-david-mcdonald/
**Resume PDF:** /warren-mcdonald-resume.pdf

## Live Ingested Resume Data (Dynamic Storage Sync)
{result}
"""

    _active_resume_text = formatted_resume
    _last_file_hash = new_hash

    telemetry.record_event("RESUME_HOT_RELOADED", f"Successfully reloaded resume (SHA256: {new_hash[:8]}...)")
    logger.info(f"Resume successfully hot-reloaded! (Hash: {new_hash[:12]}...)")
    return True, "Resume successfully parsed and hot-reloaded into memory."

def get_current_resume() -> str:
    """Returns the current active resume text (dynamic or fallback)."""
    return _active_resume_text

