from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.dmarc import DMARCReport, DMARCReportSummary
from .elasticsearch import es_service
from .dmarc_parser import dmarc_parser
from .third_party_service import third_party_service_identifier
import uuid

class DMARCService:
    def ingest_report(self, xml_content: str, customer_id: str) -> str:
        try:
            report = dmarc_parser.parse_xml_report(xml_content, customer_id)
            report_id = str(uuid.uuid4())
            
            for record in report.records:
                # Skip third-party service identification for now
                if not hasattr(record, 'third_party_service') or record.third_party_service is None:
                    record.third_party_service = "unknown"
            
            report_doc = report.dict()
            es_service.index_document("reports", report_id, report_doc)
            
            return report_id
        except Exception as e:
            raise ValueError(f"Failed to ingest DMARC report: {str(e)}")
    
    def get_reports_summary(self, customer_id: str, days: int = 7) -> DMARCReportSummary:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"customer_id": customer_id}},
                        {"range": {
                            "metadata.date_range_begin": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        }}
                    ]
                }
            },
            "aggs": {
                "records": {
                    "nested": {
                        "path": "records"
                    },
                    "aggs": {
                        "total_emails": {
                            "sum": {
                                "field": "records.count"
                            }
                        },
                        "passed_emails": {
                            "filter": {
                                "term": {"records.dmarc_result": "pass"}
                            },
                            "aggs": {
                                "count": {
                                    "sum": {
                                        "field": "records.count"
                                    }
                                }
                            }
                        },
                        "services": {
                            "terms": {
                                "field": "records.third_party_service",
                                "size": 10,
                                "missing": "unknown"
                            },
                            "aggs": {
                                "email_count": {
                                    "sum": {
                                        "field": "records.count"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        result = es_service.search_documents("reports", query)
        aggs = result.get("aggregations", {})
        records_agg = aggs.get("records", {})
        
        total_emails = int(records_agg.get("total_emails", {}).get("value", 0))
        passed_emails = int(records_agg.get("passed_emails", {}).get("count", {}).get("value", 0))
        failed_emails = total_emails - passed_emails
        pass_rate = (passed_emails / total_emails * 100) if total_emails > 0 else 0
        
        top_services = []
        for bucket in records_agg.get("services", {}).get("buckets", []):
            top_services.append({
                "service": bucket["key"],
                "email_count": bucket["email_count"]["value"]
            })
        
        return DMARCReportSummary(
            total_emails=total_emails,
            passed_emails=passed_emails,
            failed_emails=failed_emails,
            pass_rate=round(pass_rate, 2),
            date_range={
                "start": start_date,
                "end": end_date
            },
            top_services=top_services
        )
    
    def get_reports_by_customer(self, customer_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        query = {
            "query": {
                "term": {"customer_id": customer_id}
            },
            "sort": [
                {"processed_at": {"order": "desc"}}
            ]
        }
        
        result = es_service.search_documents("reports", query, size=limit)
        reports = []
        for hit in result["hits"]["hits"]:
            report_data = hit["_source"]
            report_data["id"] = hit["_id"]
            reports.append(report_data)
        
        return reports
    
    def get_time_series_data(self, customer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"customer_id": customer_id}},
                        {"range": {
                            "metadata.date_range_begin": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        }}
                    ]
                }
            },
            "aggs": {
                "daily_stats": {
                    "date_histogram": {
                        "field": "metadata.date_range_begin",
                        "calendar_interval": "day"
                    },
                    "aggs": {
                        "records": {
                            "nested": {
                                "path": "records"
                            },
                            "aggs": {
                                "total_emails": {
                                    "sum": {
                                        "field": "records.count"
                                    }
                                },
                                "passed_emails": {
                                    "filter": {
                                        "term": {"records.dmarc_result": "pass"}
                                    },
                                    "aggs": {
                                        "count": {
                                            "sum": {
                                                "field": "records.count"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        result = es_service.search_documents("reports", query)
        daily_data = []
        
        for bucket in result.get("aggregations", {}).get("daily_stats", {}).get("buckets", []):
            records_agg = bucket.get("records", {})
            total = int(records_agg.get("total_emails", {}).get("value", 0))
            passed = int(records_agg.get("passed_emails", {}).get("count", {}).get("value", 0))
            
            daily_data.append({
                "date": bucket["key_as_string"],
                "total_emails": total,
                "passed_emails": passed,
                "failed_emails": total - passed,
                "pass_rate": (passed / total * 100) if total > 0 else 0
            })
        
        return daily_data

dmarc_service = DMARCService()