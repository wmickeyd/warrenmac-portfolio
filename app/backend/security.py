"""
HTTP-layer security controls shared across endpoints:
1. Trusted-proxy client IP resolution (rate limits can't be bypassed with a spoofed X-Forwarded-For)
2. Browser security headers (CSP, HSTS, framing, MIME sniffing)
3. Constant-time secret comparison
"""

import hmac
import os

from fastapi import Request

def is_production() -> bool:
    return os.getenv("ENVIRONMENT") == "production" or os.getenv("STORAGE_BACKEND") == "gcs"

def get_client_ip(request: Request) -> str:
    """
    Resolves the real client IP behind a known number of trusted proxies.

    The Google Cloud load balancer appends "<client-ip>, <lb-ip>" to whatever X-Forwarded-For
    the client sent, so only the rightmost XFF_TRUSTED_HOPS entries can be trusted. Taking the
    first entry (as many apps do) lets any caller pick their own IP and evade per-IP rate limits.
    With XFF_TRUSTED_HOPS=0 (local / no proxy) the header is ignored entirely.
    """
    fallback = request.client.host if request.client else "127.0.0.1"
    try:
        hops = int(os.getenv("XFF_TRUSTED_HOPS", "0"))
    except ValueError:
        hops = 0
    if hops <= 0:
        return fallback

    entries = [e.strip() for e in request.headers.get("x-forwarded-for", "").split(",") if e.strip()]
    if len(entries) < hops:
        return fallback
    return entries[-hops]

def secrets_match(provided: str, expected: str) -> bool:
    """Constant-time comparison; an unset expected value never matches (fail closed)."""
    if not expected:
        return False
    return hmac.compare_digest(provided.encode(), expected.encode())

CONTENT_SECURITY_POLICY = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self' data:",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
])

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    if is_production():
        # TLS terminates at the load balancer; browsers only honour HSTS over HTTPS anyway
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
