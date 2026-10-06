"""Report queries must name fields that exist in the reports index mapping. A field the
mapping lacks (e.g. `customer_id.keyword` on a plain keyword field) matches nothing, so
the dashboard silently shows zero emails."""
from unittest.mock import patch

from app.services.dmarc_service import dmarc_service
from app.services.elasticsearch import es_service


def mapped_fields(props, prefix=""):
    for name, spec in props.items():
        path = prefix + name
        yield path
        yield from (f"{path}.{sub}" for sub in spec.get("fields", {}))
        yield from mapped_fields(spec.get("properties", {}), path + ".")


def queried_fields(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("term", "range") and isinstance(value, dict):
                yield from value.keys()
            elif key == "field" and isinstance(value, str):
                yield value
            elif key == "sort" and isinstance(value, list):
                yield from (k for s in value for k in s)
            else:
                yield from queried_fields(value)
    elif isinstance(node, list):
        for item in node:
            yield from queried_fields(item)


def test_report_queries_use_mapped_fields():
    _, mapping = es_service._get_dmarc_reports_index()
    known = set(mapped_fields(mapping["properties"]))
    with patch.object(es_service, "search_documents", return_value={"hits": {"hits": []}}) as search:
        dmarc_service.get_reports_summary("cust", 7, "example.com")
        dmarc_service.get_reports_by_customer("cust", 10, "example.com")
        dmarc_service.get_time_series_data("cust", 30, "example.com")
    used = {f for call in search.call_args_list for f in queried_fields(call.args[1])}
    assert {"customer_id", "policy.domain", "records.dmarc_result"} <= used
    assert used <= known, f"not in the reports mapping: {sorted(used - known)}"
