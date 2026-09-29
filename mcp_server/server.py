"""Read-only MCP server for the DMARC Analytics API.

Talks only to the HTTP API as a normal user, so every call inherits JWT auth,
per-customer scoping and rate limits. It never touches Elasticsearch directly.
"""
import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

API_URL = os.environ.get("DMARC_API_URL", "http://localhost:8000/api/v1").rstrip("/")
READ_ONLY = ToolAnnotations(readOnlyHint=True)

mcp = MCPServer("dmarc")
client = httpx.Client(base_url=API_URL, timeout=30)
_token: str | None = None


def _login() -> None:
    # ponytail: password from env; switch to scoped long-lived API keys if this ships to customers
    global _token
    r = client.post("/auth/login", json={
        "email": os.environ["DMARC_EMAIL"],
        "password": os.environ["DMARC_PASSWORD"],
    })
    _raise_for_status(r)
    _token = r.json()["access_token"]


def _raise_for_status(r: httpx.Response) -> None:
    if r.is_error:
        try:
            detail = r.json().get("detail", r.text)
        except (ValueError, AttributeError):
            detail = r.text
        # ToolError text reaches the client; other exceptions are masked by the SDK
        raise ToolError(f"DMARC API {r.status_code}: {detail}")


def _get(path: str, **params: Any) -> Any:
    """GET an API path as the configured user, re-logging in once if the token expired."""
    global _token
    params = {k: v for k, v in params.items() if v is not None}
    for attempt in range(2):
        try:
            if _token is None:
                _login()
            r = client.get(path, params=params, headers={"Authorization": f"Bearer {_token}"})
        except httpx.TransportError as e:
            raise ToolError(f"DMARC API unreachable at {API_URL}: {e}") from e
        if r.status_code == 401 and attempt == 0:
            _token = None
            continue
        _raise_for_status(r)
        return r.json()


@mcp.tool(annotations=READ_ONLY)
def get_summary(days: int = 7, domain: str | None = None) -> dict:
    """Email totals, pass/fail counts, pass rate and top sending services for the last N days (1-365), optionally for one domain."""
    return _get("/dmarc/summary", days=days, domain=domain)


@mcp.tool(annotations=READ_ONLY)
def get_time_series(days: int = 30, domain: str | None = None) -> list:
    """Daily pass/fail email volumes for the last N days (1-365), optionally for one domain."""
    return _get("/dmarc/time-series", days=days, domain=domain)


@mcp.tool(annotations=READ_ONLY)
def list_reports(limit: int = 20, domain: str | None = None) -> list:
    """Most recent DMARC aggregate reports with per-source-IP SPF/DKIM/DMARC results."""
    reports = _get("/dmarc/reports", limit=limit, domain=domain)
    for report in reports:
        report.pop("raw_xml", None)  # large and redundant with the parsed records
    return reports


@mcp.tool(annotations=READ_ONLY)
def get_detailed_report(days: int = 30) -> dict:
    """Full analytics report for the last N days (1-365): compliance score, failure breakdowns, trends and recommendations."""
    return _get("/analytics/detailed-report", days=days)


@mcp.tool(annotations=READ_ONLY)
def list_alerts(days: int = 7) -> list:
    """Security alerts (failure-rate spikes, volume anomalies, suspicious sources) from the last N days (1-30)."""
    return _get("/alerts/", days=days)


@mcp.tool(annotations=READ_ONLY)
def list_domains() -> list:
    """Domains monitored for this account."""
    return _get("/domains/")


if __name__ == "__main__":
    mcp.run()
