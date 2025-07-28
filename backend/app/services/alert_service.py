from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.dmarc import DMARCReport
from .elasticsearch import es_service
from .dmarc_service import dmarc_service
import uuid
import asyncio

class AlertService:
    def __init__(self):
        self.alert_thresholds = {
            'high_failure_rate': 50.0,  # Alert if failure rate > 50%
            'volume_spike': 2.0,        # Alert if volume increases by 200%
            'unknown_sender_threshold': 10,  # Alert if >10 emails from unknown senders
            'suspicious_countries': ['CN', 'RU', 'KP', 'IR']  # Suspicious countries
        }
    
    async def check_alerts_for_customer(self, customer_id: str) -> List[Dict[str, Any]]:
        alerts = []
        
        # Check for high failure rates
        failure_rate_alert = await self._check_high_failure_rate(customer_id)
        if failure_rate_alert:
            alerts.append(failure_rate_alert)
        
        # Check for volume spikes
        volume_spike_alert = await self._check_volume_spike(customer_id)
        if volume_spike_alert:
            alerts.append(volume_spike_alert)
        
        # Check for unknown senders
        unknown_sender_alert = await self._check_unknown_senders(customer_id)
        if unknown_sender_alert:
            alerts.append(unknown_sender_alert)
        
        # Check for geographic anomalies
        geo_anomaly_alert = await self._check_geographic_anomalies(customer_id)
        if geo_anomaly_alert:
            alerts.append(geo_anomaly_alert)
        
        # Store alerts
        for alert in alerts:
            await self._store_alert(alert)
        
        return alerts
    
    async def _check_high_failure_rate(self, customer_id: str) -> Optional[Dict[str, Any]]:
        try:
            summary = await dmarc_service.get_reports_summary(customer_id, days=1)
            
            if summary.pass_rate < (100 - self.alert_thresholds['high_failure_rate']):
                return {
                    'id': str(uuid.uuid4()),
                    'customer_id': customer_id,
                    'alert_type': 'high_failure_rate',
                    'severity': 'high',
                    'title': 'High DMARC Failure Rate Detected',
                    'description': f'DMARC authentication failure rate is {100 - summary.pass_rate:.1f}% (threshold: {self.alert_thresholds["high_failure_rate"]}%)',
                    'data': {
                        'pass_rate': summary.pass_rate,
                        'failed_emails': summary.failed_emails,
                        'total_emails': summary.total_emails
                    },
                    'created_at': datetime.utcnow().isoformat(),
                    'resolved': False
                }
        except Exception:
            pass
        
        return None
    
    async def _check_volume_spike(self, customer_id: str) -> Optional[Dict[str, Any]]:
        try:
            today_summary = await dmarc_service.get_reports_summary(customer_id, days=1)
            week_summary = await dmarc_service.get_reports_summary(customer_id, days=7)
            
            avg_daily_volume = week_summary.total_emails / 7
            spike_threshold = avg_daily_volume * self.alert_thresholds['volume_spike']
            
            if today_summary.total_emails > spike_threshold and avg_daily_volume > 0:
                return {
                    'id': str(uuid.uuid4()),
                    'customer_id': customer_id,
                    'alert_type': 'volume_spike',
                    'severity': 'medium',
                    'title': 'Email Volume Spike Detected',
                    'description': f'Email volume increased to {today_summary.total_emails} (average: {avg_daily_volume:.0f})',
                    'data': {
                        'current_volume': today_summary.total_emails,
                        'average_volume': avg_daily_volume,
                        'spike_ratio': today_summary.total_emails / avg_daily_volume if avg_daily_volume > 0 else 0
                    },
                    'created_at': datetime.utcnow().isoformat(),
                    'resolved': False
                }
        except Exception:
            pass
        
        return None
    
    async def _check_unknown_senders(self, customer_id: str) -> Optional[Dict[str, Any]]:
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"customer_id": customer_id}},
                            {"range": {
                                "processed_at": {
                                    "gte": start_date.isoformat(),
                                    "lte": end_date.isoformat()
                                }
                            }}
                        ]
                    }
                },
                "aggs": {
                    "unknown_senders": {
                        "nested": {"path": "records"},
                        "aggs": {
                            "filter_unknown": {
                                "filter": {
                                    "bool": {
                                        "must_not": [
                                            {"exists": {"field": "records.third_party_service"}}
                                        ]
                                    }
                                },
                                "aggs": {
                                    "total_emails": {
                                        "sum": {"field": "records.count"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            result = await es_service.search_documents("reports", query)
            unknown_emails = result.get("aggregations", {}).get("unknown_senders", {}).get("filter_unknown", {}).get("total_emails", {}).get("value", 0)
            
            if unknown_emails > self.alert_thresholds['unknown_sender_threshold']:
                return {
                    'id': str(uuid.uuid4()),
                    'customer_id': customer_id,
                    'alert_type': 'unknown_senders',
                    'severity': 'medium',
                    'title': 'Unknown Email Senders Detected',
                    'description': f'{int(unknown_emails)} emails from unidentified senders in the last 24 hours',
                    'data': {
                        'unknown_email_count': int(unknown_emails)
                    },
                    'created_at': datetime.utcnow().isoformat(),
                    'resolved': False
                }
        except Exception:
            pass
        
        return None
    
    async def _check_geographic_anomalies(self, customer_id: str) -> Optional[Dict[str, Any]]:
        # This would require GeoIP database integration
        # For now, return None - can be implemented with MaxMind GeoIP2
        return None
    
    async def _store_alert(self, alert: Dict[str, Any]):
        alert_id = alert['id']
        await es_service.index_document("alerts", alert_id, alert)
    
    async def get_alerts_for_customer(self, customer_id: str, days: int = 7) -> List[Dict[str, Any]]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"customer_id": customer_id}},
                        {"range": {
                            "created_at": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        }}
                    ]
                }
            },
            "sort": [
                {"created_at": {"order": "desc"}}
            ]
        }
        
        result = await es_service.search_documents("alerts", query)
        alerts = []
        for hit in result["hits"]["hits"]:
            alert_data = hit["_source"]
            alerts.append(alert_data)
        
        return alerts
    
    async def resolve_alert(self, alert_id: str) -> bool:
        try:
            alert = await es_service.get_document("alerts", alert_id)
            if not alert:
                return False
            
            alert_data = alert["_source"]
            alert_data["resolved"] = True
            alert_data["resolved_at"] = datetime.utcnow().isoformat()
            
            await es_service.index_document("alerts", alert_id, alert_data)
            return True
        except Exception:
            return False
    
    async def run_periodic_checks(self):
        """Run periodic alert checks for all customers"""
        # Get all unique customer IDs
        query = {
            "aggs": {
                "customers": {
                    "terms": {
                        "field": "customer_id",
                        "size": 1000
                    }
                }
            },
            "size": 0
        }
        
        try:
            result = await es_service.search_documents("reports", query)
            customer_buckets = result.get("aggregations", {}).get("customers", {}).get("buckets", [])
            
            for bucket in customer_buckets:
                customer_id = bucket["key"]
                alerts = await self.check_alerts_for_customer(customer_id)
                
                if alerts:
                    print(f"Generated {len(alerts)} alerts for customer {customer_id}")
                
                # Add small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
        except Exception as e:
            print(f"Error running periodic checks: {e}")

alert_service = AlertService()