"""Managed SPF routes, with the control plane, Elasticsearch and DNS faked."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import get_current_active_user
from app.core.config import settings
from app.main import app
from app.models.user import User, UserRole
from app.services.spf_flattening_service import SpfFlatteningService, check_transport, spf_flattening_service as spf

FQDN = "example-com-abc123.spf.test"


def user(role):
    return User(id="u", email="u@test.example", role=role, customer_id="cust",
                is_active=True, created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00")


@pytest.fixture
def fake(monkeypatch):
    """In-memory mappings, policies and live SPF; returns them for assertions."""
    state = {"mappings": {}, "policies": {}, "puts": [], "live": "v=spf1 -all"}
    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_URL", "https://cp.test")
    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_TOKEN", "t")
    monkeypatch.setattr(settings, "SPF_ZONE", "spf.test.")
    monkeypatch.setattr(spf, "get_mapping", lambda c, d: state["mappings"].get((c, d)))

    def ensure(c, d):
        return state["mappings"].setdefault((c, d), {"customer_id": c, "domain": d, "fqdn": FQDN})
    monkeypatch.setattr(spf, "ensure_mapping", ensure)
    monkeypatch.setattr(spf, "delete_mapping", lambda c, d: state["mappings"].pop((c, d)))

    async def call(method, fqdn, body=None):
        if method == "PUT":
            if "bad.example" in body["senders"]:
                raise HTTPException(status_code=400, detail="invalid sender domain")
            state["puts"].append(body["senders"])
            state["policies"][fqdn] = {"senders": body["senders"], "terms": ["ip4:192.0.2.1"],
                                       "records": 1, "last_error": None}
        if method == "DELETE":
            state["policies"].pop(fqdn, None)
        return state["policies"].get(fqdn)
    monkeypatch.setattr(spf, "_call", call)

    async def live(domain):
        return state["live"]
    monkeypatch.setattr(spf, "live_spf", live)
    return state


def client_as(role):
    app.dependency_overrides[get_current_active_user] = lambda: user(role)
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_publish_status_and_delete(fake):
    c = client_as(UserRole.ADMIN)
    assert c.get("/api/v1/spf/example.com").json() == {"domain": "example.com", "configured": False}

    r = c.put("/api/v1/spf/example.com", json={"senders": ["_spf.google.com", " 192.0.2.1 "]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert fake["puts"] == [["_spf.google.com", "192.0.2.1"]]
    assert body["include"] == FQDN and body["lookups"] == 1 and body["installed"] is False
    assert body["suggested_record"] == f"v=spf1 include:{FQDN} -all"

    # Publishing again reuses the same name
    c.put("/api/v1/spf/example.com", json={"senders": ["sendgrid.net"]})
    assert len(fake["mappings"]) == 1

    # Control-plane validation errors reach the user
    r = c.put("/api/v1/spf/example.com", json={"senders": ["bad.example"]})
    assert r.status_code == 400

    # Can't delete while the customer's SPF still includes it: that would be a permerror
    fake["live"] = f"v=spf1 include:{FQDN} ~all"
    assert c.get("/api/v1/spf/example.com").json()["installed"] is True
    assert c.delete("/api/v1/spf/example.com").status_code == 409
    fake["live"] = "v=spf1 -all"
    assert c.delete("/api/v1/spf/example.com").status_code == 200
    assert fake["mappings"] == {} and fake["policies"] == {}


def test_read_only_can_view_but_not_write(fake):
    c = client_as(UserRole.READ_ONLY)
    assert c.get("/api/v1/spf/example.com").status_code == 200
    assert c.put("/api/v1/spf/example.com", json={"senders": ["sendgrid.net"]}).status_code == 403
    assert c.delete("/api/v1/spf/example.com").status_code == 403


def test_unconfigured_is_503(monkeypatch):
    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_URL", None)
    c = client_as(UserRole.ADMIN)
    assert c.put("/api/v1/spf/example.com", json={"senders": ["sendgrid.net"]}).status_code == 503


def test_transport_and_record_parsing():
    check_transport("https://cp.example.net", False)
    check_transport("http://127.0.0.1:8054", False)
    check_transport("http://localhost:8054", False)
    check_transport("http://cp.internal:8053", True)
    for bad in ["http://cp.example.net", "ftp://cp.example.net", "cp.example.net"]:
        with pytest.raises(ValueError):
            check_transport(bad, False)

    assert SpfFlatteningService.includes("v=spf1 +include:x.spf.test. -all", "x.spf.test")
    assert not SpfFlatteningService.includes("v=spf1 include:x.spf.test.evil -all", "x.spf.test")
    assert not SpfFlatteningService.includes("google-site-verification=x", "x.spf.test")
    assert SpfFlatteningService.suggested_record("", "x.spf.test") == "v=spf1 include:x.spf.test ~all"


# ---- connection status and test (system admins) ----

import httpx
from app.services import spf_flattening_service as sfs
from app.services.spf_flattening_service import grant_matches

REAL_ASYNC_CLIENT = httpx.AsyncClient


def fake_control_plane(monkeypatch, whoami=None, zones=("spf.test.",), whoami_status=200):
    """Points the service at a fake control plane answering /whoami and /zones."""
    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_URL", "https://cp.test")
    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_TOKEN", "secret-token")
    monkeypatch.setattr(settings, "SPF_ZONE", "spf.test.")
    whoami = whoami or {"name": "dmarc-app", "admin": False, "expires_at": None,
                        "grants": [{"pattern": "spf.test.", "role": "editor", "scripts": False}]}

    def handler(req):
        assert req.headers["authorization"] == "Bearer secret-token"
        if req.url.path == "/whoami":
            return httpx.Response(whoami_status, json=whoami)
        return httpx.Response(200, json={"seq": 1, "zones": [{"name": z} for z in zones]})
    monkeypatch.setattr(sfs.httpx, "AsyncClient",
                        lambda **kw: REAL_ASYNC_CLIENT(transport=httpx.MockTransport(handler), **kw))


def statuses(body):
    return {c["name"]: c["status"] for c in body["checks"]}


def test_connection_status_and_test(monkeypatch):
    fake_control_plane(monkeypatch)
    c = client_as(UserRole.SYSTEM_ADMIN)
    st = c.get("/api/v1/spf/admin/status").json()
    assert st["configured"] and st["zone"] == "spf.test." and st["token_set"]
    assert "secret-token" not in str(st)

    body = c.post("/api/v1/spf/admin/test").json()
    assert body["ok"], body
    assert set(statuses(body).values()) == {"pass"}
    assert len(body["checks"]) == 6


def test_connection_test_explains_failures(monkeypatch):
    c = client_as(UserRole.SYSTEM_ADMIN)

    fake_control_plane(monkeypatch, whoami_status=401)
    body = c.post("/api/v1/spf/admin/test").json()
    assert not body["ok"] and statuses(body)["Token"] == "fail"

    fake_control_plane(monkeypatch, whoami={"name": "ro", "admin": False, "expires_at": None,
                                            "grants": [{"pattern": "*.test.", "role": "viewer"}]})
    body = c.post("/api/v1/spf/admin/test").json()
    assert statuses(body)["Can edit SPF zone"] == "fail" and "viewer" in body["checks"][-1]["detail"]

    fake_control_plane(monkeypatch, zones=())
    assert statuses(c.post("/api/v1/spf/admin/test").json())["Zone exists"] == "fail"

    # Admin or expiring tokens work but are flagged
    fake_control_plane(monkeypatch, whoami={"name": "root", "admin": True, "expires_at": "2027-01-01", "grants": []})
    body = c.post("/api/v1/spf/admin/test").json()
    assert body["ok"] and statuses(body)["Token"] == "warn" and statuses(body)["Can edit SPF zone"] == "warn"

    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_URL", "http://cp.example.net")
    monkeypatch.setattr(settings, "DNS_CONTROL_PLANE_ALLOW_HTTP", False)
    assert statuses(c.post("/api/v1/spf/admin/test").json())["Secure transport"] == "fail"

    monkeypatch.setattr(settings, "SPF_ZONE", None)
    body = c.post("/api/v1/spf/admin/test").json()
    assert body["checks"] == [{"name": "Settings", "status": "fail",
                               "detail": "Set SPF_ZONE in .env and restart the API"}]


def test_connection_routes_need_system_admin(monkeypatch):
    fake_control_plane(monkeypatch)
    c = client_as(UserRole.ADMIN)
    assert c.get("/api/v1/spf/admin/status").status_code == 403
    assert c.post("/api/v1/spf/admin/test").status_code == 403


def test_grant_matching():
    assert grant_matches("*", "spf.test.")
    assert grant_matches("spf.test.", "spf.test.")
    assert grant_matches("*.test.", "spf.test.")
    assert not grant_matches("*.spf.test.", "spf.test.")  # below the apex only
    assert not grant_matches("other.test.", "spf.test.")
    assert not grant_matches("*.st.", "spf.test.")
