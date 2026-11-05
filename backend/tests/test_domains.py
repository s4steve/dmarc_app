"""Domains live in Elasticsearch, per customer, so they survive an API restart."""
from unittest.mock import MagicMock, patch

from elasticsearch import ConflictError
from fastapi.testclient import TestClient

from app.api import domains
from app.api.auth import get_current_active_user
from app.main import app
from app.models.user import User, UserRole


def as_customer(customer_id):
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id="u", email="u@test.example", role=UserRole.ADMIN, customer_id=customer_id, is_active=True,
        created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00")
    return TestClient(app)


class FakeStore:
    """The parts of es_service domains.py uses, keeping documents outside the API process"""
    index_prefix = "dmarc"

    def __init__(self):
        self.docs = {}
        self.client = MagicMock()
        self.client.create.side_effect = self.create

    def create(self, index, id, document, refresh=None):
        assert index == "dmarc-domains"
        if id in self.docs:
            raise ConflictError("exists", MagicMock(status=409), {})
        self.docs[id] = document

    def search_documents(self, index, query, size=100):
        terms = query["query"]["bool"]["filter"] if "bool" in query["query"] else [query["query"]]
        wanted = {k: v for t in terms for k, v in t["term"].items()}
        return {"hits": {"hits": [{"_id": i, "_source": d} for i, d in sorted(self.docs.items())
                                  if all(d[k] == v for k, v in wanted.items())]}}

    def delete_document(self, index, doc_id, refresh=None):
        del self.docs[doc_id]


def test_domains_are_stored_per_customer_and_can_be_deleted():
    store = FakeStore()
    try:
        with patch.object(domains, "es_service", store):
            client = as_customer("a")
            created = client.post("/api/v1/domains/", json={"name": "example.com"}).json()
            assert "customer_id" not in created
            assert client.post("/api/v1/domains/", json={"name": "example.com"}).status_code == 409
            # What the API held in memory is gone: a fresh read comes from the store
            assert [d["name"] for d in client.get("/api/v1/domains/").json()] == ["example.com"]

            other = as_customer("b")
            assert other.get("/api/v1/domains/").json() == []
            assert other.delete(f"/api/v1/domains/{created['id']}").status_code == 404
            assert other.post("/api/v1/domains/", json={"name": "example.com"}).status_code == 200

            client = as_customer("a")
            assert client.delete(f"/api/v1/domains/{created['id']}").status_code == 200
            assert client.get("/api/v1/domains/").json() == []
    finally:
        app.dependency_overrides.clear()
