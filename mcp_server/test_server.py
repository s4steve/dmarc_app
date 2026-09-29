import os

import httpx

os.environ.setdefault("DMARC_EMAIL", "mcp@example.com")
os.environ.setdefault("DMARC_PASSWORD", "test-password")

import server  # noqa: E402


def _mock(handler):
    server.client = httpx.Client(base_url="http://api/api/v1", transport=httpx.MockTransport(handler))
    server._token = None


def test_expired_token_triggers_one_relogin_and_retry():
    logins, calls = [], []

    def handler(request):
        if request.url.path == "/api/v1/auth/login":
            logins.append(1)
            return httpx.Response(200, json={"access_token": f"tok{len(logins)}"})
        calls.append(request.headers["Authorization"])
        if request.headers["Authorization"] == "Bearer tok1":
            return httpx.Response(401, json={"detail": "expired"})
        return httpx.Response(200, json={"pass_rate": 99.0})

    _mock(handler)
    assert server.get_summary(days=7) == {"pass_rate": 99.0}
    assert len(logins) == 2
    assert calls == ["Bearer tok1", "Bearer tok2"]


def test_list_reports_strips_raw_xml_and_drops_none_params():
    def handler(request):
        if request.url.path == "/api/v1/auth/login":
            return httpx.Response(200, json={"access_token": "tok"})
        assert "domain" not in request.url.params
        return httpx.Response(200, json=[{"report_id": "r1", "raw_xml": "<feedback/>"}])

    _mock(handler)
    assert server.list_reports() == [{"report_id": "r1"}]


def test_api_errors_surface_detail():
    def handler(request):
        if request.url.path == "/api/v1/auth/login":
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(422, json={"detail": "days must be <= 365"})

    _mock(handler)
    try:
        server.get_summary(days=999)
    except server.ToolError as e:
        assert "422" in str(e) and "365" in str(e)
    else:
        raise AssertionError("expected ToolError")
