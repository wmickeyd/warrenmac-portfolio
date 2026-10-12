import pytest
from unittest.mock import patch, MagicMock
import mlflow_client

def test_mlflow_disabled_by_default(monkeypatch):
    monkeypatch.setattr(mlflow_client, "MLFLOW_TRACKING_URI", "")
    monkeypatch.setattr(mlflow_client, "_mlflow_available", False)
    assert not mlflow_client.is_mlflow_enabled()
    
    # Should not throw any exception
    mlflow_client.init_mlflow()
    mlflow_client.log_chat_trace(
        user_prompt="test",
        ai_response="test response",
        status="ok",
        client_ip="127.0.0.1",
        latency_ms=12.5
    )
    mlflow_client.log_resume_sync_event(
        file_hash="abc12345",
        char_count=500,
        status_message="OK",
        storage_backend="local"
    )

def test_mlflow_fail_open_on_unreachable_server(monkeypatch):
    monkeypatch.setattr(mlflow_client, "MLFLOW_TRACKING_URI", "http://127.0.0.1:59999")
    
    # Should safely catch exception and set _mlflow_available = False
    with patch("mlflow.set_tracking_uri", side_effect=Exception("Connection refused")):
        mlflow_client.init_mlflow()
        assert not mlflow_client._mlflow_available
        
        # Logging trace should fail-open without raising
        mlflow_client.log_chat_trace(
            user_prompt="test",
            ai_response="test response",
            status="blocked",
            client_ip="127.0.0.1",
            latency_ms=5.0,
            guardrail_reason="Injection detected"
        )

def test_mlflow_trace_span_recording(monkeypatch):
    monkeypatch.setattr(mlflow_client, "MLFLOW_TRACKING_URI", "http://localhost:5001")
    
    mock_span = MagicMock()
    mock_mlflow = MagicMock()
    mock_mlflow.start_span.return_value.__enter__.return_value = mock_span
    
    monkeypatch.setattr(mlflow_client, "_mlflow_available", True)
    monkeypatch.setattr(mlflow_client, "_mlflow_module", mock_mlflow)
    
    mlflow_client.log_chat_trace(
        user_prompt="Explain Kubernetes architecture",
        ai_response="Kubernetes is an orchestration platform...",
        status="ok",
        client_ip="192.168.1.50",
        latency_ms=145.2,
        guardrail_reason="",
        model_name="gemini-flash-lite-latest",
        canary_token_present=True
    )
    
    mock_mlflow.start_span.assert_called_once_with(name="portfolio_chat")
    mock_span.set_inputs.assert_called_once_with({
        "prompt": "Explain Kubernetes architecture",
        "client_ip": "192.168.1.50"
    })
    mock_span.set_outputs.assert_called_once_with({
        "response": "Kubernetes is an orchestration platform...",
        "status": "ok",
        "guardrail_reason": ""
    })

