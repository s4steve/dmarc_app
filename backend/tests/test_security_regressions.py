"""
Regression tests for the security remediation. They run without Elasticsearch or Redis:
Redis is fakeredis (see conftest.offline_infra) and the user store is an in-memory dict.
"""
import gzip
import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import UserInDB, UserRole
from app.core.security import get_password_hash
from app.services.session_service import session_service
from app.services.user_service import user_service
from app.middleware.rate_limiter import get_authenticated_user_key

PASSWORD = "correct-horse-battery"
NOW = "2026-01-01T00:00:00"
HASH = get_password_hash(PASSWORD)

def make_user(email, role, customer_id="acme", is_active=True):
    return UserInDB(
        id=email.split("@")[0], email=email, role=role, customer_id=customer_id,
        is_active=is_active, hashed_password=HASH, created_at=NOW, updated_at=NOW,
    )

@pytest.fixture
def users():
    return {
        u.email: u for u in [
            make_user("sys@x.com", UserRole.SYSTEM_ADMIN, customer_id="default"),
            make_user("admin@acme.com", UserRole.ADMIN),
            make_user("viewer@acme.com", UserRole.READ_ONLY),
        ]
    }

@pytest.fixture
def client(users):
    async def by_email(email):
        return users.get(email)
    # conftest.offline_infra already supplies fakeredis and in-memory rate limits
    with patch.object(user_service, "get_user_by_email", side_effect=by_email):
        yield TestClient(app, raise_server_exceptions=False)

def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})

def auth(client, email):
    r = login(client, email)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# --- Authentication -------------------------------------------------------

def test_old_hardcoded_credentials_rejected(client):
    assert login(client, "admin@example.com", "admin123").status_code == 401

def test_real_user_can_log_in(client):
    r = client.get("/api/v1/users/me", headers=auth(client, "admin@acme.com"))
    assert r.status_code == 200 and r.json()["email"] == "admin@acme.com"

def test_wrong_password_rejected(client):
    assert login(client, "admin@acme.com", "nope-nope-nope").status_code == 401

def test_deactivated_user_loses_access_immediately(client, users):
    headers = auth(client, "viewer@acme.com")
    users["viewer@acme.com"].is_active = False
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    assert login(client, "viewer@acme.com").status_code == 401

def test_login_rate_limited(client):
    codes = [login(client, "x@x.com", "wrong-password").status_code for _ in range(6)]
    assert codes[:5] == [401] * 5 and codes[5] == 429

# --- Sessions ---------------------------------------------------------------

def test_token_rejected_after_logout(client):
    headers = auth(client, "admin@acme.com")
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401

def test_logout_all_revokes_every_session(client):
    h1, h2 = auth(client, "admin@acme.com"), auth(client, "admin@acme.com")
    assert client.get("/api/v1/auth/sessions", headers=h1).json()["total_count"] == 2
    assert client.post("/api/v1/auth/logout-all", headers=h1).status_code == 200
    assert client.get("/api/v1/users/me", headers=h1).status_code == 401
    assert client.get("/api/v1/users/me", headers=h2).status_code == 401
    # Only hashes are stored, never raw tokens
    token = h2["Authorization"].split()[1]
    assert not any(token in (session_service.redis.get(k) or "") for k in session_service.redis.keys("*")
                   if session_service.redis.type(k) == "string")

def test_revocation_check_fails_closed_when_redis_down(client):
    headers = auth(client, "admin@acme.com")
    with patch.object(session_service.redis, "exists", side_effect=ConnectionError("redis down")):
        assert client.get("/api/v1/users/me", headers=headers).status_code == 401

def test_rate_limit_key_differs_per_token():
    class Req:
        def __init__(self, token):
            self.headers = {"authorization": f"Bearer {token}"}
            self.client = type("C", (), {"host": "1.2.3.4"})()
    # Both tokens share the JWT header prefix "eyJhbGci" that the old key used
    assert get_authenticated_user_key(Req("eyJhbGciAAAA")) != get_authenticated_user_key(Req("eyJhbGciBBBB"))

# --- Access control --------------------------------------------------------

def test_tenant_admin_cannot_create_system_admin(client):
    r = client.post("/api/v1/users/", headers=auth(client, "admin@acme.com"), json={
        "email": "evil@acme.com", "password": "long-enough-password", "customer_id": "acme",
        "role": "system_admin",
    })
    assert r.status_code == 403

def test_tenant_admin_cannot_promote_to_system_admin(client, users):
    async def by_id(user_id):
        return users["viewer@acme.com"]
    with patch.object(user_service, "get_user_by_id", side_effect=by_id), \
         patch.object(user_service, "update_user") as update:
        r = client.put("/api/v1/users/viewer", headers=auth(client, "admin@acme.com"), json={"role": "system_admin"})
    assert r.status_code == 403 and not update.called

def test_tenant_admin_cannot_modify_global_services(client):
    headers = auth(client, "admin@acme.com")
    assert client.put("/api/v1/services/admin/svc1", headers=headers, json={"is_active": False}).status_code == 403
    assert client.post("/api/v1/services/initialize", headers=headers).status_code == 403
    # The old unvalidated tenant-level route is gone
    assert client.put("/api/v1/services/svc1", headers=headers, json={"x": 1}).status_code in (404, 405)

def test_cannot_resolve_another_customers_alert(client):
    other = {"_source": {"customer_id": "other-customer", "resolved": False}}
    with patch("app.services.alert_service.es_service.get_document", return_value=other), \
         patch("app.services.alert_service.es_service.index_document") as index:
        r = client.post("/api/v1/alerts/a1/resolve", headers=auth(client, "admin@acme.com"))
    assert r.status_code == 404 and not index.called

# --- Uploads ----------------------------------------------------------------

def upload(client, headers, name, data):
    return client.post("/api/v1/dmarc/upload-report", headers=headers,
                       files={"file": (name, io.BytesIO(data), "application/xml")})

def test_oversized_upload_rejected(client):
    r = upload(client, auth(client, "admin@acme.com"), "big.xml", b"a" * (10 * 1024 * 1024 + 10))
    assert r.status_code == 413

def test_gzip_bomb_rejected(client):
    bomb = gzip.compress(b"\0" * (60 * 1024 * 1024))  # ~60 KB compressed, 60 MB expanded
    assert upload(client, auth(client, "admin@acme.com"), "bomb.xml.gz", bomb).status_code == 413

def test_xxe_doctype_rejected(client):
    xxe = b'<?xml version="1.0"?><!DOCTYPE f [<!ENTITY x SYSTEM "file:///etc/passwd">]><feedback>&x;</feedback>'
    with patch("app.api.dmarc.dmarc_service.ingest_report") as ingest:
        r = upload(client, auth(client, "admin@acme.com"), "xxe.xml", xxe)
    assert r.status_code == 400 and not ingest.called

# --- Input validation and error disclosure -----------------------------------

def test_malicious_domain_rejected(client):
    r = client.post("/api/v1/domains/", headers=auth(client, "admin@acme.com"), json={"name": "a.com'; drop"})
    assert r.status_code == 400

def test_500_responses_hide_exception_details(client):
    with patch("app.api.alerts.alert_service.get_alerts_for_customer",
               side_effect=RuntimeError("/srv/secret/path dmarc-reports index")):
        r = client.get("/api/v1/alerts/", headers=auth(client, "admin@acme.com"))
    assert r.status_code == 500
    assert "secret" not in r.text and "dmarc-reports" not in r.text
