import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.models.user import User



def test_scan_domain_as_admin(auth_headers):
    client = TestClient(app)
    response = client.post(
        "/api/v1/dns-scanner/scan-domain/",
        headers=auth_headers,
        json={"domain": "google.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "google.com"
    assert "dmarc" in data
    assert "spf" in data
    assert "dkim" in data

def test_scan_domain_as_non_admin(auth_headers):
    client = TestClient(app)
    response = client.post(
        "/api/v1/dns-scanner/scan-domain/",
        headers=auth_headers,
        json={"domain": "google.com"},
    )
    assert response.status_code == 403

def test_scan_domain_with_no_token():
    client = TestClient(app)
    response = client.post(
        "/api/v1/dns-scanner/scan-domain/",
        json={"domain": "google.com"},
    )
    assert response.status_code == 401

def test_scan_domain_with_invalid_body():
    client = TestClient(app)
    response = client.post(
        "/api/v1/dns-scanner/scan-domain/",
        json={"not_a_domain": "google.com"},
    )
    assert response.status_code == 422
