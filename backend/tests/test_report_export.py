"""The analytics report's numbers and its CSV and PDF downloads."""
import asyncio
import csv
import io
import re
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.auth import get_current_active_user
from app.main import app
from app.models.user import User, UserRole
from app.services import report_export
from app.services.analytics_service import analytics_service

REPORT = {
    "period": {"start": "2026-10-01T00:00:00", "end": "2026-10-31T00:00:00", "days": 30},
    "basic_metrics": {"total_emails": 1200, "dmarc_pass_rate": 90.0, "spf_pass_rate": 80.5, "dkim_pass_rate": 85.25, "unique_sources": 7},
    "trend_analysis": {"daily_trends": [{"date": "2026-10-01T00:00:00.000Z", "volume": 1200, "pass_rate": 90.0},
                                        {"date": "2026-10-02T00:00:00.000Z", "volume": 0, "pass_rate": 0}],
                       "summary": {"volume_growth_7d": 12.5}},
    "service_performance": {"services": [{"service": "Mailchimp (EU)", "volume": 1000, "pass_rate": 99.0, "failed_emails": 10},
                                         {"service": "=HYPERLINK(1)", "volume": 200, "pass_rate": 50.0, "failed_emails": 100}]},
    "threat_intelligence": {"suspicious_sources": [{"ip": "192.0.2.1", "failed_emails": 110}]},
    "compliance_score": {"overall_score": 88.0, "level": "Good", "recommendations": ["Improve SPF"]},
}


def rows(text):
    return list(csv.reader(io.StringIO(text)))


def test_csv_has_each_section():
    out = rows(report_export.to_csv(REPORT))
    assert out[0] == ["DMARC report", "2026-10-01 to 2026-10-31"]
    assert ["Emails in reports", "1200"] in out and ["Passed DMARC", "90.0%"] in out
    assert ["Emails this week vs last", "+12.5%"] in out
    assert ["Mailchimp (EU)", "1000", "99.0%", "10"] in out
    assert ["192.0.2.1", "110"] in out
    assert ["2026-10-01", "1200", "90.0%"] in out
    assert ["2026-10-02", "0", "n/a"] in out   # no email that day is not a 0% pass rate
    assert ["Improve SPF"] in out


def test_unmatched_servers_are_named_as_the_app_names_them():
    report = {**REPORT, "service_performance": {"services": [{"service": "unknown", "volume": 5, "pass_rate": 0.0, "failed_emails": 5}]}}
    assert ["Unrecognised servers", "5", "0.0%", "5"] in rows(report_export.to_csv(report))


def test_csv_neutralises_spreadsheet_formulas():
    assert ["'=HYPERLINK(1)", "200", "50.0%", "100"] in rows(report_export.to_csv(REPORT))


def test_exports_survive_a_failed_or_empty_report():
    empty = {"period": {}, "basic_metrics": {}, "trend_analysis": {}, "service_performance": {},
             "threat_intelligence": {}, "compliance_score": {"overall_score": None, "level": "No recent reports"}}
    out = rows(report_export.to_csv(empty))
    assert ["Rating, last 7 days", "No recent reports"] in out and ["Score, last 7 days", "n/a"] in out
    assert ["Emails this week vs last", "n/a"] in out
    assert report_export.to_pdf(empty).startswith(b"%PDF-")


def check_pdf(pdf):
    """The cross-reference table is what readers navigate by, so every offset has to be exact"""
    assert pdf.startswith(b"%PDF-1.4\n") and pdf.endswith(b"%%EOF\n")
    xref = int(re.search(rb"startxref\n(\d+)\n", pdf).group(1))
    assert pdf[xref:xref + 5] == b"xref\n"
    offsets = re.findall(rb"(\d{10}) 00000 n ", pdf[xref:])
    for number, offset in enumerate(offsets, 1):
        assert pdf[int(offset):].startswith(b"%d 0 obj\n" % number)
    for declared, body in re.findall(rb"<< /Length (\d+) >>\nstream\n(.*?)\nendstream", pdf, re.S):
        assert int(declared) == len(body)
    return len(offsets)


def test_pdf_is_well_formed_and_escapes_text():
    pdf = report_export.to_pdf(REPORT)
    check_pdf(pdf)
    assert b"(Mailchimp \\(EU\\)) Tj" in pdf and b"(1,000) Tj" in pdf


def test_pdf_flows_onto_more_pages_and_replaces_other_alphabets():
    days = [{"date": f"2026-01-{i:02}", "volume": 5, "pass_rate": 100.0} for i in range(1, 29)] * 5
    long = {**REPORT, "trend_analysis": {"daily_trends": days},
            "service_performance": {"services": [{"service": "日本語メール", "volume": 1, "pass_rate": 0.0, "failed_emails": 1}]}}
    pdf = report_export.to_pdf(long)
    objects = check_pdf(pdf)
    pages = (objects - 4) // 2
    assert pages > 1 and pdf.count(b"/Type /Page ") == pages and b"/Count %d" % pages in pdf
    assert b"(??????) Tj" in pdf


def test_routes_download_files():
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id="u", email="u@test.example", role=UserRole.READ_ONLY, customer_id="cust", is_active=True,
        created_at="2026-01-01T00:00:00", updated_at="2026-01-01T00:00:00")
    try:
        with patch.object(analytics_service, "get_detailed_report", AsyncMock(return_value=REPORT)) as get:
            client = TestClient(app)
            for fmt, media, start in (("csv", "text/csv", b"DMARC report"), ("pdf", "application/pdf", b"%PDF-")):
                r = client.get(f"/api/v1/analytics/export/{fmt}?days=30")
                assert r.status_code == 200 and r.headers["content-type"].startswith(media)
                assert r.headers["content-disposition"] == f'attachment; filename="dmarc_report_30d.{fmt}"'
                assert r.content.startswith(start)
            assert get.call_args.args == ("cust", 30)
            assert client.get("/api/v1/analytics/export/json").json()["basic_metrics"]["total_emails"] == 1200
    finally:
        app.dependency_overrides.clear()


# ---- the numbers behind them ----

NOW = datetime(2026, 11, 1)


def run(coro):
    return asyncio.run(coro)


def test_service_counts_come_from_the_records():
    result = {"aggregations": {"records": {"services": {"buckets": [
        {"key": "Mailchimp", "volume": {"value": 100.0}, "passed": {"emails": {"value": 90.0}}},
        {"key": "unknown", "volume": {"value": 40.0}, "passed": {"emails": {"value": 0.0}}}]}}}}
    with patch("app.services.analytics_service.es_service.search_documents", return_value=result):
        out = run(analytics_service._get_service_performance("c", NOW, NOW))
    assert out["services"][0] == {"service": "Mailchimp", "volume": 100, "pass_rate": 90.0, "failed_emails": 10}
    assert out["total_services"] == 1 and out["unknown_volume"] == 40


def test_failing_sources_come_from_the_records():
    result = {"aggregations": {"records": {"failed": {
        "total": {"value": 150.0}, "source_count": {"value": 9},
        "high_failure": {"buckets": [{"key": "192.0.2.1"}]},
        "sources": {"buckets": [{"key": "192.0.2.1", "failures": {"value": 120.0}}]}}}}}
    with patch("app.services.analytics_service.es_service.search_documents", return_value=result):
        out = run(analytics_service._get_threat_intelligence("c", NOW, NOW))
    assert out["suspicious_sources"] == [{"ip": "192.0.2.1", "failed_emails": 120}]
    assert out["total_failed_sources"] == 9
    assert out["threat_indicators"] == {"high_failure_ips": 1, "authentication_bypass_attempts": 150}


def test_size_is_only_passed_as_a_parameter():
    # The Elasticsearch client raises if a request sets size in both the body and the parameter
    empty = {"aggregations": {"records": {"services": {"buckets": []}, "failed": {
        "total": {"value": 0}, "source_count": {"value": 0}, "high_failure": {"buckets": []}, "sources": {"buckets": []}}}}}
    with patch("app.services.analytics_service.es_service.search_documents", return_value=empty) as search:
        run(analytics_service._get_service_performance("c", NOW, NOW))
        run(analytics_service._get_threat_intelligence("c", NOW, NOW))
    assert search.call_count == 2
    for call in search.call_args_list:
        assert "size" not in call.args[1] and call.kwargs["size"] == 0


def test_no_recent_mail_is_not_a_poor_score():
    with patch.object(analytics_service, "_get_basic_metrics", AsyncMock(return_value={"total_emails": 0})):
        out = run(analytics_service._calculate_compliance_score("c"))
    assert out["overall_score"] is None and out["level"] == "No recent reports" and out["recommendations"] == []
