"""
MLflow Observability & GenAI Tracing Client
Provides LLM request tracing, guardrail telemetry, and resume ingestion tracking.
Designed to fail-open: if MLflow is not configured or unavailable, application performance is untouched.
"""

import os
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("mlflow_client")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "warrenmac-portfolio")

_mlflow_available = False
_mlflow_module = None

def is_mlflow_enabled() -> bool:
    """Checks if MLflow tracking is configured via environment."""
    return bool(MLFLOW_TRACKING_URI)

def init_mlflow():
    """Initializes MLflow configuration if MLFLOW_TRACKING_URI is set."""
    global _mlflow_available, _mlflow_module
    if not is_mlflow_enabled():
        logger.info("MLflow tracking disabled (MLFLOW_TRACKING_URI not set).")
        return

    try:
        import mlflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        _mlflow_module = mlflow
        _mlflow_available = True
        logger.info(f"MLflow initialized: URI='{MLFLOW_TRACKING_URI}', Experiment='{MLFLOW_EXPERIMENT_NAME}'")
    except Exception as e:
        _mlflow_available = False
        logger.warning(f"Could not connect to MLflow tracking server ({e}). Operating in fail-open mode.")

def log_chat_trace(
    user_prompt: str,
    ai_response: str,
    status: str,  # "ok" or "blocked"
    client_ip: str,
    latency_ms: float,
    guardrail_reason: str = "",
    model_name: str = "gemini-flash-lite-latest",
    canary_token_present: bool = True
):
    """
    Logs an OpenTelemetry-compatible GenAI span in MLflow Tracing.
    Captures prompt, response, latency, and guardrail verdicts.
    """
    if not _mlflow_available or _mlflow_module is None:
        return

    try:
        span_name = "portfolio_chat" if status == "ok" else "portfolio_chat_blocked"
        with _mlflow_module.start_span(name=span_name) as span:
            span.set_inputs({
                "prompt": user_prompt,
                "client_ip": client_ip,
            })
            span.set_outputs({
                "response": ai_response,
                "status": status,
                "guardrail_reason": guardrail_reason
            })
            span.set_attributes({
                "llm.model_name": model_name,
                "llm.status": status,
                "latency_ms": round(latency_ms, 2),
                "guardrail.passed": (status == "ok"),
                "guardrail.rejection_reason": guardrail_reason or "None",
                "guardrail.canary_protected": canary_token_present,
            })
    except Exception as e:
        logger.warning(f"Non-blocking MLflow trace recording error: {e}")

def log_resume_sync_event(
    file_hash: str,
    char_count: int,
    status_message: str,
    storage_backend: str
):
    """Logs resume ingestion / hot-reloading events as an MLflow run."""
    if not _mlflow_available or _mlflow_module is None:
        return

    try:
        with _mlflow_module.start_run(run_name=f"resume_sync_{file_hash[:8]}", nested=True):
            _mlflow_module.log_params({
                "storage_backend": storage_backend,
                "sha256": file_hash,
            })
            _mlflow_module.log_metrics({
                "resume_characters": char_count,
            })
            _mlflow_module.set_tag("event_type", "resume_ingestion")
            _mlflow_module.set_tag("status", status_message)
    except Exception as e:
        logger.warning(f"Non-blocking MLflow resume sync recording error: {e}")

