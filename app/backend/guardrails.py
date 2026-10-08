"""
AI DevSecOps Guardrails Engine
Implements defense-in-depth for LLM applications:
1. Pre-execution Prompt Injection & Jailbreak detection (OWASP LLM01)
2. Canary token leak prevention (detects system prompt exfiltration)
3. Post-execution DLP / Secret scrubbing (OWASP LLM06)
4. Client IP rate limiting & Denial of Wallet protection (OWASP LLM04)
"""

import re
import time
import secrets
from typing import Tuple, Dict, Any, List
from collections import defaultdict

# Cryptographic canary token generated per backend lifecycle
CANARY_TOKEN = f"CANARY_SEC_{secrets.token_hex(8).upper()}"

# Common prompt injection and jailbreak signatures
INJECTION_PATTERNS = [
    r"(?i)ignore (all )?(previous|above|prior) (instructions|directions|rules)",
    r"(?i)disregard (all )?(previous|above|prior)",
    r"(?i)system prompt",
    r"(?i)reveal (your|the) (instructions|prompt|rules|hidden)",
    r"(?i)you are now (in )?(developer mode|DAN|unrestricted|jailbreak)",
    r"(?i)pretend you (are|have) no (limits|rules|filters)",
    r"(?i)bypass (safety|content|security) filters",
    r"(?i)print (your )?(entire )?(initial|system|hidden) (prompt|message)",
    r"(?i)output (everything|the text) above",
    r"(?i)repeat the words above",
    r"(?i)what (is|are) your (initial|system) instructions",
    r"(?i)canary_token",
]

# Sensitive patterns that should never leak out to users
SENSITIVE_PATTERNS = [
    r"AIza[0-9A-Za-z-_]{35}",                    # Google API Keys
    r"(?i)canary_sec_[0-9a-f]{16}",              # System prompt canary token
    r"192\.168\.\d{1,3}\.\d{1,3}",              # Cluster Internal IPs
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}",           # VPC Internal IPs
    r"cluster\.local",                           # Kubernetes internal domain
]

class SecurityTelemetry:
    """Tracks live security events for the public DevSecOps dashboard."""
    def __init__(self):
        self.total_requests = 0
        self.blocked_injections = 0
        self.canary_leaks_prevented = 0
        self.rate_limits_triggered = 0
        self.successful_queries = 0
        self.recent_events: List[Dict[str, Any]] = []

    def record_event(self, event_type: str, details: str):
        event = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": event_type,
            "details": details
        }
        self.recent_events.insert(0, event)
        if len(self.recent_events) > 50:
            self.recent_events.pop()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_queries": self.successful_queries,
            "blocked_injections": self.blocked_injections,
            "canary_leaks_prevented": self.canary_leaks_prevented,
            "rate_limits_triggered": self.rate_limits_triggered,
            "recent_events": self.recent_events[:10]
        }

telemetry = SecurityTelemetry()

class RateLimiter:
    """Sliding-window IP rate limiter to protect LLM inference costs."""
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Clean older requests outside window
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < self.window_seconds
        ]
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        self.requests[client_ip].append(now)
        return True

rate_limiter = RateLimiter(max_requests=12, window_seconds=60)

def validate_input(user_prompt: str, client_ip: str) -> Tuple[bool, str]:
    """
    Ingress inspection: checks rate limit, length, and prompt injection signatures.
    Returns (is_valid, error_or_reason).
    """
    telemetry.total_requests += 1

    # 1. Rate Limiting Check
    if not rate_limiter.is_allowed(client_ip):
        telemetry.rate_limits_triggered += 1
        telemetry.record_event("RATE_LIMIT", f"IP {client_ip} exceeded window limit")
        return False, "Rate limit exceeded. Please wait a minute before asking another question."

    # 2. Payload Length Check (Prevent context-stuffing DoS)
    if len(user_prompt) > 800:
        telemetry.blocked_injections += 1
        telemetry.record_event("PAYLOAD_TOO_LARGE", f"Prompt length {len(user_prompt)} exceeded limit")
        return False, "Prompt is too long. Please keep your question under 800 characters."

    # 3. Prompt Injection / Jailbreak Detection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_prompt):
            telemetry.blocked_injections += 1
            telemetry.record_event(
                "PROMPT_INJECTION_BLOCKED",
                f"Matched pattern: {pattern}"
            )
            return False, "Security Notice: Your query triggered the AI DevSecOps prompt injection guardrail. Please ask a direct question about Warren's resume or experience."

    return True, ""

def sanitize_output(raw_response: str) -> Tuple[bool, str]:
    """
    Egress inspection: checks for canary token leaks and scrubs secrets/internal IPs.
    Returns (is_safe, sanitized_content).
    """
    # 1. Canary Token Check (Detects system prompt exfiltration)
    if CANARY_TOKEN in raw_response:
        telemetry.canary_leaks_prevented += 1
        telemetry.record_event("CANARY_TOKEN_LEAK_PREVENTED", "Model attempted to leak system instructions")
        return False, "Security Notice: Output blocked by egress guardrail (system prompt exfiltration attempt intercepted)."

    # 2. Secret & Internal Network PII Scrubbing
    sanitized = raw_response
    for pattern in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED_BY_GUARDRAIL]", sanitized)

    telemetry.successful_queries += 1
    return True, sanitized

