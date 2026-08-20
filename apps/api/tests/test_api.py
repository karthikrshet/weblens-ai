"""
Integration tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "WebLens AI"


def test_health_and_ready():
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    res_ready = client.get("/api/v1/ready")
    assert res_ready.status_code == 200


def test_ssrf_rejection_on_analyze():
    response = client.post(
        "/api/v1/websites/analyze",
        json={"url": "http://127.0.0.1:8000"},
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()


def test_invalid_scheme_rejection():
    response = client.post(
        "/api/v1/websites/analyze",
        json={"url": "file:///etc/passwd"},
    )
    assert response.status_code == 400
    assert "scheme" in response.json()["detail"].lower()
