"""The analytics report as a CSV or PDF download."""
import csv
import io
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple

from .analytics_service import UNKNOWN


NOT_AVAILABLE = "n/a"


def _pct(value: Optional[float]) -> str:
    return NOT_AVAILABLE if value is None else f"{value:.1f}%"


def _sections(report: Dict[str, Any]) -> List[Tuple[str, List[str], List[List[Any]]]]:
    """(title, column headings, rows) for each part of the report. A part whose query failed is
    empty rather than missing, so both formats keep the same shape."""
    basic = report.get("basic_metrics") or {}
    services = (report.get("service_performance") or {}).get("services") or []
    threats = report.get("threat_intelligence") or {}
    trends = report.get("trend_analysis") or {}
    score = report.get("compliance_score") or {}
    growth = (trends.get("summary") or {}).get("volume_growth_7d")
    return [
        ("Summary", ["Measure", "Value"], [
            ["Emails in reports", basic.get("total_emails", 0)],
            ["Passed DMARC", _pct(basic.get("dmarc_pass_rate"))],
            ["Passed SPF", _pct(basic.get("spf_pass_rate"))],
            ["Passed DKIM", _pct(basic.get("dkim_pass_rate"))],
            ["Sending servers", basic.get("unique_sources", 0)],
            ["Emails this week vs last", NOT_AVAILABLE if growth is None else f"{growth:+.1f}%"],
            ["Score, last 7 days", score.get("overall_score") if score.get("overall_score") is not None else NOT_AVAILABLE],
            ["Rating, last 7 days", score.get("level", "")],
        ]),
        ("Senders", ["Sender", "Emails", "Passed DMARC", "Failed"], [
            ["Unrecognised servers" if s["service"] == UNKNOWN else s["service"], s["volume"], _pct(s["pass_rate"]), s["failed_emails"]]
            for s in services]),
        ("Servers failing DMARC most", ["Server IP", "Failed emails"], [
            [s["ip"], s["failed_emails"]] for s in threats.get("suspicious_sources") or []]),
        ("Each day", ["Date", "Emails", "Passed DMARC"], [
            [t["date"][:10], t["volume"], _pct(t["pass_rate"]) if t["volume"] else NOT_AVAILABLE]
            for t in trends.get("daily_trends") or []]),
        ("Recommendations", ["Recommendation"], [[r] for r in score.get("recommendations") or []]),
    ]


def _period(report: Dict[str, Any]) -> str:
    period = report.get("period") or {}
    return f"{str(period.get('start', ''))[:10]} to {str(period.get('end', ''))[:10]}"


def _safe_cell(value: Any) -> Any:
    # Report contents come from whoever emails a report, and a spreadsheet runs a cell starting
    # with one of these as a formula. Our own percentages, such as +1.5%, are left alone.
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r") \
            and not re.fullmatch(r"[+-][\d.]+%", value):
        return "'" + value
    return value


def to_csv(report: Dict[str, Any]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["DMARC report", _period(report)])
    for title, headings, rows in _sections(report):
        writer.writerow([])
        writer.writerow([title])
        writer.writerow(headings)
        writer.writerows([_safe_cell(c) for c in row] for row in rows)
    return out.getvalue()


# ponytail: a hand-written PDF of text and the two fonts every reader has, which is all this
# report needs and adds no dependency. Move to reportlab if it ever needs charts or Unicode beyond
# Western European (other characters print as "?").
PAGE_W, PAGE_H, MARGIN = 595, 842, 50  # A4, in points
COLUMNS = {1: [0], 2: [0, 320], 3: [0, 170, 300], 4: [0, 230, 320, 420]}


def _pdf_text(x: float, y: float, text: Any, size: int, bold: bool) -> bytes:
    raw = str(text).encode("cp1252", "replace").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    return b"BT /F%d %d Tf %g %g Td (%s) Tj ET\n" % (2 if bold else 1, size, x, y, raw)


def _pdf_pages(report: Dict[str, Any]) -> List[bytes]:
    pages, page, y = [], [], PAGE_H - MARGIN

    def line(cells: List[Tuple[float, Any]], size: int = 10, bold: bool = False, gap: int = 15) -> None:
        nonlocal page, y
        if y < MARGIN:
            pages.append(b"".join(page))
            page, y = [], PAGE_H - MARGIN
        page.extend(_pdf_text(MARGIN + x, y, text, size, bold) for x, text in cells)
        y -= gap

    line([(0, "DMARC report")], size=20, bold=True, gap=24)
    line([(0, _period(report))], gap=12)
    for title, headings, rows in _sections(report):
        y -= 14
        if not rows:
            continue
        # A heading stays with the start of its table
        if y < MARGIN + 60:
            y = MARGIN - 1
        line([(0, title)], size=13, bold=True, gap=18)
        xs = COLUMNS[len(headings)]
        if len(headings) == 1:
            for row in rows:
                for wrapped in textwrap.wrap(str(row[0]), 90):
                    line([(0, wrapped)])
            continue
        line(list(zip(xs, headings)), bold=True)
        for row in rows:
            first = str(row[0])
            cells = [first if len(first) <= 38 else first[:37] + "..."] + row[1:]
            line(list(zip(xs, [f"{c:,}" if isinstance(c, int) else c for c in cells])))
    pages.append(b"".join(page))
    return pages


def to_pdf(report: Dict[str, Any]) -> bytes:
    contents = _pdf_pages(report)
    # Objects: 1 catalog, 2 page list, 3 and 4 fonts, then a page and its content for each page
    kids = " ".join(f"{5 + 2 * i} 0 R" for i in range(len(contents)))
    font = "<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(contents)} >>".encode(),
        (font % "Helvetica").encode(),
        (font % "Helvetica-Bold").encode(),
    ]
    for i, content in enumerate(contents):
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                       f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {6 + 2 * i} 0 R >>".encode())
        objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content))
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return bytes(out)
