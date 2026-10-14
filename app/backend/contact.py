"""
Contact form delivery: forwards consulting inquiries to Warren's inbox via the Resend HTTPS API.
Resend runs over 443, which the pod's egress NetworkPolicy already allows (SMTP ports are blocked).
"""

import os
import httpx

from guardrails import RateLimiter

RESEND_API_URL = "https://api.resend.com/emails"

# Tight per-IP window: legitimate clients send one inquiry, not dozens
contact_rate_limiter = RateLimiter(max_requests=3, window_seconds=600)

def _config():
    return (
        os.getenv("RESEND_API_KEY", ""),
        os.getenv("CONTACT_TO_EMAIL", ""),
        os.getenv("CONTACT_FROM_EMAIL", ""),
    )

def is_configured() -> bool:
    return all(_config())

def _single_line(value: str) -> str:
    """Collapse CR/LF so user input can't inject extra email headers via the subject."""
    return " ".join(value.splitlines()).strip()

async def send_contact_email(name: str, email: str, company: str, message: str) -> bool:
    """Sends the inquiry as a plain-text email with Reply-To set to the visitor. Returns True on success."""
    api_key, to_email, from_email = _config()
    clean_name = _single_line(name)
    clean_company = _single_line(company)

    body = (
        f"Name: {clean_name}\n"
        f"Email: {email}\n"
        f"Company: {clean_company or '-'}\n\n"
        f"{message}\n"
    )
    payload = {
        "from": from_email,
        "to": [to_email],
        "reply_to": email,
        "subject": f"Consulting inquiry from {clean_name}",
        "text": body,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                RESEND_API_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if res.is_success:
            return True
        print(f"Contact email delivery failed: Resend returned HTTP {res.status_code}")
    except httpx.HTTPError as e:
        print(f"Contact email delivery failed: {type(e).__name__}")
    return False
