"""Managed SPF: publishes each domain's flattened sender list on the dns_server_db control
plane, which keeps it refreshed. The customer adds one `include:<fqdn>` to their own SPF."""
import ipaddress
import logging
import re
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import dns.asyncresolver
import dns.exception
import dns.resolver
import httpx
from elasticsearch import ConflictError
from fastapi import HTTPException

from ..core.config import settings
from .elasticsearch import es_service

logger = logging.getLogger(__name__)

INDEX = "spf_policies"


def check_transport(url: str, allow_http: bool) -> None:
    """The bearer token may only travel over https, except to loopback or when allowed.
    Mirrors check_transport() in dns_server_db's dns-server and mcp-server."""
    parts = urlsplit(url)
    if parts.scheme == "https":
        return
    if parts.scheme != "http":
        raise ValueError(f"DNS_CONTROL_PLANE_URL must be https://, not {parts.scheme or 'missing'}")
    host = parts.hostname or ""
    try:
        loopback = host == "localhost" or ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if not (loopback or allow_http):
        raise ValueError(
            "DNS_CONTROL_PLANE_URL must be https:// for a non-loopback host "
            "(set DNS_CONTROL_PLANE_ALLOW_HTTP=1 only for development)"
        )


def _zone() -> str:
    return settings.SPF_ZONE.strip().rstrip(".").lower()


ROLES = ["viewer", "editor", "owner"]


def grant_matches(pattern: str, zone: str) -> bool:
    """Whether a control-plane grant pattern covers `zone` (both lowercase, trailing dot):
    `zone.` itself, `*.parent.` for zones strictly below parent, or `*` for every zone.
    Mirrors Grant::matches in dns_server_db's control-plane/src/auth.rs."""
    if pattern == "*":
        return True
    if pattern.startswith("*."):
        return zone.endswith(pattern[1:]) and zone != pattern[2:]
    return zone == pattern


def _spf_terms(txt: str) -> Optional[List[str]]:
    """The lowercased terms of an SPF record, or None if it isn't one."""
    terms = txt.lower().split()
    return terms[1:] if terms and terms[0] == "v=spf1" else None


class SpfFlatteningService:
    def _configured(self) -> str:
        if not (settings.DNS_CONTROL_PLANE_URL and settings.DNS_CONTROL_PLANE_TOKEN and settings.SPF_ZONE):
            raise HTTPException(status_code=503, detail="Managed SPF is not configured")
        try:
            check_transport(settings.DNS_CONTROL_PLANE_URL, settings.DNS_CONTROL_PLANE_ALLOW_HTTP)
        except ValueError as e:
            logger.error(str(e))
            raise HTTPException(status_code=503, detail="Managed SPF is misconfigured")
        return settings.DNS_CONTROL_PLANE_URL.rstrip("/")

    async def _call(self, method: str, fqdn: str, body: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """One control-plane call. None for 404; its validation errors become 400s."""
        # Trailing dot: the control plane reads names without one as relative to the zone
        url = f"{self._configured()}/zones/{_zone()}/spf/{fqdn}."
        headers = {"Authorization": f"Bearer {settings.DNS_CONTROL_PLANE_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.request(method, url, json=body, headers=headers)
        except httpx.HTTPError as e:
            logger.error(f"DNS control plane unreachable: {e}")
            raise HTTPException(status_code=502, detail="DNS control plane unreachable")
        if r.status_code == 404:
            return None
        if r.status_code == 400:
            try:
                errors = r.json().get("errors") or []
            except ValueError:
                errors = []
            raise HTTPException(status_code=400, detail="; ".join(errors) or "Rejected by the DNS control plane")
        if r.status_code >= 300:
            # 401/403 here mean the app's token is wrong: an operator problem, not the user's
            logger.error(f"DNS control plane {method} {url}: {r.status_code} {r.text[:500]}")
            raise HTTPException(status_code=502, detail="DNS control plane error")
        return r.json()

    # ---- connection status, for system admins ----

    def status(self) -> Dict[str, Any]:
        """The connection settings as the API sees them. Never includes the token."""
        url = settings.DNS_CONTROL_PLANE_URL or None
        transport_error = None
        if url:
            try:
                check_transport(url, settings.DNS_CONTROL_PLANE_ALLOW_HTTP)
            except ValueError as e:
                transport_error = str(e)
        return {
            "configured": bool(url and settings.DNS_CONTROL_PLANE_TOKEN and settings.SPF_ZONE),
            "url": url,
            "zone": settings.SPF_ZONE or None,
            "token_set": bool(settings.DNS_CONTROL_PLANE_TOKEN),
            "allow_http": settings.DNS_CONTROL_PLANE_ALLOW_HTTP,
            "transport_error": transport_error,
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Checks each step publishing needs, in order, stopping at the first failure."""
        checks: List[Dict[str, str]] = []

        def check(name: str, status: str, detail: str) -> bool:
            checks.append({"name": name, "status": status, "detail": detail})
            return status != "fail"

        def result() -> Dict[str, Any]:
            return {"ok": all(c["status"] != "fail" for c in checks), "checks": checks}

        st = self.status()
        missing = [k for k, v in (("DNS_CONTROL_PLANE_URL", st["url"]), ("DNS_CONTROL_PLANE_TOKEN", st["token_set"]),
                                  ("SPF_ZONE", st["zone"])) if not v]
        if not check("Settings", "fail" if missing else "pass",
                     f"Set {', '.join(missing)} in .env and restart the API" if missing else "URL, token and zone are set"):
            return result()
        if not check("Secure transport", "fail" if st["transport_error"] else "pass",
                     st["transport_error"] or ("https" if st["url"].startswith("https://") else "plain http allowed")):
            return result()

        base = st["url"].rstrip("/")
        zone = _zone() + "."
        headers = {"Authorization": f"Bearer {settings.DNS_CONTROL_PLANE_TOKEN}"}
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get(f"{base}/whoami", headers=headers)
            except httpx.HTTPError as e:
                check("Reachable", "fail", f"Couldn't connect to {base}: {e.__class__.__name__} {e}".strip())
                return result()
            check("Reachable", "pass", f"{base} answered")
            if r.status_code == 401:
                check("Token", "fail", "The control plane rejected the token: it is wrong, revoked or expired")
                return result()
            if r.status_code != 200:
                check("Token", "fail", f"/whoami returned HTTP {r.status_code}; is this a dns_server_db control plane?")
                return result()
            me = r.json()
            expires = me.get("expires_at")
            if expires:
                check("Token", "warn", f"Accepted as {me.get('name')}, but it expires {expires}. "
                      "Mint one with `control-plane create-token` so it doesn't.")
            else:
                check("Token", "pass", f"Accepted as {me.get('name')}; never expires")

            if me.get("admin"):
                check("Can edit SPF zone", "warn", f"Yes, but the token is an admin on every zone. "
                      f"Use one that is editor on {zone} only.")
            else:
                roles = [g.get("role") for g in me.get("grants", []) if grant_matches(g.get("pattern", ""), zone)]
                best = max(roles, key=lambda x: ROLES.index(x) if x in ROLES else -1, default=None)
                if best not in ("editor", "owner"):
                    check("Can edit SPF zone", "fail", f"The token is {best or 'not granted anything'} on {zone}; "
                          "it needs editor")
                    return result()
                check("Can edit SPF zone", "pass", f"{best} on {zone}")

            r = await client.get(f"{base}/zones", headers=headers)
            names = {z.get("name", "").lower().rstrip(".") + "." for z in r.json().get("zones", [])} if r.status_code == 200 else set()
            check("Zone exists", "pass" if zone in names else "fail",
                  f"{zone} is hosted" if zone in names else
                  f"{zone} doesn't exist on the control plane; create it with POST /zones")
        return result()

    # ---- (customer, domain) -> fqdn mapping ----

    def get_mapping(self, customer_id: str, domain: str) -> Optional[Dict[str, Any]]:
        doc = es_service.get_document(INDEX, f"{customer_id}:{domain}")
        return doc["_source"] if doc else None

    def ensure_mapping(self, customer_id: str, domain: str) -> Dict[str, Any]:
        """The domain's policy name, created on first use. Names are unguessable because
        domains aren't verified: a name derived from the domain alone would let one
        customer set the senders another customer's SPF includes."""
        existing = self.get_mapping(customer_id, domain)
        if existing:
            return existing
        slug = re.sub(r"[^a-z0-9]+", "-", domain.lower()).strip("-")[:40]
        mapping = {
            "customer_id": customer_id,
            "domain": domain,
            "fqdn": f"{slug}-{secrets.token_hex(3)}.{_zone()}",
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            es_service.client.create(
                index=f"{es_service.index_prefix}-{INDEX}", id=f"{customer_id}:{domain}",
                document=mapping, refresh="true",
            )
        except ConflictError:  # a concurrent request created it first
            return self.get_mapping(customer_id, domain)
        return mapping

    def delete_mapping(self, customer_id: str, domain: str) -> None:
        es_service.delete_document(INDEX, f"{customer_id}:{domain}", refresh="true")

    # ---- control plane ----

    async def get_policy(self, fqdn: str) -> Optional[Dict[str, Any]]:
        return await self._call("GET", fqdn)

    async def put_policy(self, fqdn: str, senders: List[str]) -> Dict[str, Any]:
        return await self._call("PUT", fqdn, {"senders": senders})

    async def delete_policy(self, fqdn: str) -> None:
        await self._call("DELETE", fqdn)

    # ---- the customer's live SPF ----

    async def live_spf(self, domain: str) -> Optional[str]:
        """The domain's published SPF record ("" if none). None if DNS couldn't be read."""
        try:
            answers = await dns.asyncresolver.resolve(domain, "TXT", lifetime=5)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return ""
        except dns.exception.DNSException:
            return None
        for rdata in answers:
            txt = b"".join(rdata.strings).decode(errors="replace")
            if _spf_terms(txt) is not None:
                return txt
        return ""

    @staticmethod
    def includes(spf: str, fqdn: str) -> bool:
        return any(t.lstrip("+").rstrip(".") == f"include:{fqdn}" for t in _spf_terms(spf) or [])

    @staticmethod
    def suggested_record(spf: Optional[str], fqdn: str) -> str:
        """`v=spf1 include:<fqdn>` plus the domain's current `all` term (default ~all)."""
        all_term = next((t for t in _spf_terms(spf or "") or [] if t.lstrip("+-~?") == "all"), "~all")
        return f"v=spf1 include:{fqdn} {all_term}"


spf_flattening_service = SpfFlatteningService()
