"""
Test Suite for the Contact Form Endpoint & Email Delivery
"""

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

import contact
from main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "company": "Analytical Engines Ltd",
    "message": "We'd like help hardening our Kubernetes platform.",
}

@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("CONTACT_TO_EMAIL", "owner@example.com")
    monkeypatch.setenv("CONTACT_FROM_EMAIL", "Portfolio Contact <contact@example.com>")
    contact.contact_rate_limiter.requests.clear()

@pytest.fixture
def sent(monkeypatch):
    calls = []

    async def fake_send(**kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(contact, "send_contact_email", fake_send)
    return calls

def test_contact_sends_email(sent):
    response = client.post("/api/contact", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert sent == [{
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "company": "Analytical Engines Ltd",
        "message": "We'd like help hardening our Kubernetes platform.",
    }]

def test_contact_honeypot_is_silently_dropped(sent):
    response = client.post("/api/contact", json={**VALID_PAYLOAD, "website": "http://spam.example"})
    assert response.status_code == 200
    assert sent == []

@pytest.mark.parametrize("override", [
    {"email": "not-an-email"},
    {"message": "hi"},
    {"name": ""},
])
def test_contact_rejects_invalid_payload(sent, override):
    response = client.post("/api/contact", json={**VALID_PAYLOAD, **override})
    assert response.status_code == 422
    assert sent == []

def test_contact_rate_limited(sent):
    for _ in range(3):
        assert client.post("/api/contact", json=VALID_PAYLOAD).status_code == 200
    response = client.post("/api/contact", json=VALID_PAYLOAD)
    assert response.status_code == 429
    assert len(sent) == 3

def test_contact_unconfigured_returns_503(monkeypatch, sent):
    monkeypatch.delenv("RESEND_API_KEY")
    response = client.post("/api/contact", json=VALID_PAYLOAD)
    assert response.status_code == 503
    assert sent == []

def test_contact_delivery_failure_returns_502(monkeypatch):
    async def failing_send(**kwargs):
        return False

    monkeypatch.setattr(contact, "send_contact_email", failing_send)
    response = client.post("/api/contact", json=VALID_PAYLOAD)
    assert response.status_code == 502

def _capture_resend(monkeypatch, status_code=200):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status_code, json={"id": "test"})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        contact.httpx, "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    return requests

def test_send_contact_email_builds_resend_request(monkeypatch):
    requests = _capture_resend(monkeypatch)
    ok = asyncio.run(contact.send_contact_email(
        name="Mallory\r\nBcc: victim@example.com",
        email="mallory@example.com",
        company="",
        message="Hello there, interested in consulting.",
    ))
    assert ok is True
    request = requests[0]
    assert str(request.url) == contact.RESEND_API_URL
    assert request.headers["Authorization"] == "Bearer re_test"
    body = json.loads(request.content)
    assert body["to"] == ["owner@example.com"]
    assert body["reply_to"] == "mallory@example.com"
    assert "\n" not in body["subject"] and "\r" not in body["subject"]
    assert "Hello there, interested in consulting." in body["text"]

def test_send_contact_email_returns_false_on_api_error(monkeypatch):
    _capture_resend(monkeypatch, status_code=500)
    ok = asyncio.run(contact.send_contact_email(
        name="Ada", email="ada@example.com", company="", message="Hello there, consulting?",
    ))
    assert ok is False
