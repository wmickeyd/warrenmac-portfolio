"""
Prometheus Metrics Registry for WarrenMac Portfolio & DevSecOps Platform
"""

from prometheus_client import Counter, Histogram, Gauge

# DevSecOps & AI Guardrail Telemetry
SECURITY_EVENTS_TOTAL = Counter(
    "portfolio_security_events_total",
    "Total count of DevSecOps security events detected by guardrails",
    ["event_type"]
)

# LLM Inference Telemetry
LLM_INFERENCE_DURATION_SECONDS = Histogram(
    "portfolio_llm_inference_duration_seconds",
    "Latency of Gemini AI API calls in seconds",
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
)

LLM_QUERIES_TOTAL = Counter(
    "portfolio_llm_queries_total",
    "Total LLM inference queries processed",
    ["status", "model"]
)

# Resume Engine Telemetry
RESUME_CHARACTERS = Gauge(
    "portfolio_resume_characters",
    "Character count of currently active parsed resume"
)

RESUME_SYNC_TOTAL = Counter(
    "portfolio_resume_sync_total",
    "Total resume synchronization events",
    ["status"]
)


# Contact Form Telemetry
CONTACT_SUBMISSIONS_TOTAL = Counter(
    "portfolio_contact_submissions_total",
    "Total contact form submissions by outcome",
    ["status"]
)
