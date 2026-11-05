from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..services.elasticsearch import es_service
import json

# The label for a report row no sender matched
UNKNOWN = "unknown"

class AdvancedAnalyticsService:
    @staticmethod
    def _period_filter(customer_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        return {"bool": {"filter": [
            {"term": {"customer_id": customer_id}},
            {"range": {"metadata.date_range_begin": {"gte": start_date.isoformat(), "lte": end_date.isoformat()}}}]}}

    async def get_detailed_report(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get basic metrics
        basic_metrics = await self._get_basic_metrics(customer_id, start_date, end_date)
        
        # Get trend analysis
        trend_analysis = await self._get_trend_analysis(customer_id, start_date, end_date)
        
        # Get service performance
        service_performance = await self._get_service_performance(customer_id, start_date, end_date)
        
        # Get threat intelligence
        threat_intelligence = await self._get_threat_intelligence(customer_id, start_date, end_date)
        
        # Get compliance score
        compliance_score = await self._calculate_compliance_score(customer_id)
        
        return {
            'report_id': f"analytics_{customer_id}_{int(datetime.utcnow().timestamp())}",
            'customer_id': customer_id,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'basic_metrics': basic_metrics,
            'trend_analysis': trend_analysis,
            'service_performance': service_performance,
            'threat_intelligence': threat_intelligence,
            'compliance_score': compliance_score,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def _get_basic_metrics(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get basic email authentication metrics"""
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
                "total_emails": {
                    "sum": {
                        "script": {
                            "source": "params._source.records.stream().mapToInt(record -> record.count).sum()"
                        }
                    }
                },
                "spf_pass": {
                    "sum": {
                        "script": {
                            "source": """
                            params._source.records.stream()
                                .filter(record -> record.spf_result == 'pass')
                                .mapToInt(record -> record.count).sum()
                            """
                        }
                    }
                },
                "dkim_pass": {
                    "sum": {
                        "script": {
                            "source": """
                            params._source.records.stream()
                                .filter(record -> record.dkim_result == 'pass')
                                .mapToInt(record -> record.count).sum()
                            """
                        }
                    }
                },
                "dmarc_pass": {
                    "sum": {
                        "script": {
                            "source": """
                            params._source.records.stream()
                                .filter(record -> record.dmarc_result == 'pass')
                                .mapToInt(record -> record.count).sum()
                            """
                        }
                    }
                },
                "unique_sources": {
                    "cardinality": {
                        "script": {
                            "source": "params._source.records.stream().map(record -> record.source_ip).collect(Collectors.toSet())"
                        }
                    }
                }
            }
        }
        
        try:
            result = es_service.search_documents("reports", query)
            aggs = result.get("aggregations", {})
            
            total_emails = int(aggs.get("total_emails", {}).get("value", 0))
            spf_pass = int(aggs.get("spf_pass", {}).get("value", 0))
            dkim_pass = int(aggs.get("dkim_pass", {}).get("value", 0))
            dmarc_pass = int(aggs.get("dmarc_pass", {}).get("value", 0))
            unique_sources = int(aggs.get("unique_sources", {}).get("value", 0))
            
            return {
                'total_emails': total_emails,
                'spf_pass_rate': (spf_pass / total_emails * 100) if total_emails > 0 else 0,
                'dkim_pass_rate': (dkim_pass / total_emails * 100) if total_emails > 0 else 0,
                'dmarc_pass_rate': (dmarc_pass / total_emails * 100) if total_emails > 0 else 0,
                'unique_sources': unique_sources,
                'authentication_summary': {
                    'spf_pass': spf_pass,
                    'dkim_pass': dkim_pass,
                    'dmarc_pass': dmarc_pass,
                    'spf_fail': total_emails - spf_pass,
                    'dkim_fail': total_emails - dkim_pass,
                    'dmarc_fail': total_emails - dmarc_pass
                }
            }
        except Exception:
            return {}
    
    async def _get_trend_analysis(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze trends over time"""
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
                "daily_trends": {
                    "date_histogram": {
                        "field": "metadata.date_range_begin",
                        "calendar_interval": "day"
                    },
                    "aggs": {
                        "daily_total": {
                            "sum": {
                                "script": {
                                    "source": "params._source.records.stream().mapToInt(record -> record.count).sum()"
                                }
                            }
                        },
                        "daily_pass": {
                            "sum": {
                                "script": {
                                    "source": """
                                    params._source.records.stream()
                                        .filter(record -> record.dmarc_result == 'pass')
                                        .mapToInt(record -> record.count).sum()
                                    """
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            result = es_service.search_documents("reports", query)
            daily_buckets = result.get("aggregations", {}).get("daily_trends", {}).get("buckets", [])
            
            trends = []
            total_volume = 0
            total_pass = 0
            
            for bucket in daily_buckets:
                daily_total = int(bucket["daily_total"]["value"])
                daily_pass = int(bucket["daily_pass"]["value"])
                
                total_volume += daily_total
                total_pass += daily_pass
                
                trends.append({
                    'date': bucket["key_as_string"],
                    'volume': daily_total,
                    'pass_rate': (daily_pass / daily_total * 100) if daily_total > 0 else 0
                })
            
            # Calculate growth rates
            # Comparing two weeks needs two weeks of days; None until then
            volume_growth = None
            if len(trends) >= 14:
                recent_volume = sum(t['volume'] for t in trends[-7:])
                previous_volume = sum(t['volume'] for t in trends[-14:-7])
                if previous_volume > 0:
                    volume_growth = (recent_volume - previous_volume) / previous_volume * 100
            
            return {
                'daily_trends': trends,
                'summary': {
                    'average_daily_volume': total_volume / len(trends) if trends else 0,
                    'overall_pass_rate': (total_pass / total_volume * 100) if total_volume > 0 else 0,
                    'volume_growth_7d': volume_growth
                }
            }
        except Exception:
            return {}
    
    async def _get_service_performance(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze performance by email service"""
        def emails():
            return {"sum": {"field": "records.count"}}
        query = {
            "query": self._period_filter(customer_id, start_date, end_date),
            "aggs": {"records": {"nested": {"path": "records"}, "aggs": {"services": {
                "terms": {"field": "records.third_party_service", "size": 50, "order": {"volume": "desc"}},
                "aggs": {
                    "volume": emails(),
                    "passed": {"filter": {"term": {"records.dmarc_result": "pass"}}, "aggs": {"emails": emails()}},
                }}}}},
        }
        
        try:
            result = es_service.search_documents("reports", query, size=0)
            services = []
            for bucket in result["aggregations"]["records"]["services"]["buckets"]:
                volume = int(bucket["volume"]["value"])
                passed = int(bucket["passed"]["emails"]["value"])
                services.append({
                    'service': bucket["key"],
                    'volume': volume,
                    'pass_rate': (passed / volume * 100) if volume > 0 else 0,
                    'failed_emails': volume - passed
                })
            
            return {
                'services': services,
                'total_services': len([s for s in services if s['service'] != UNKNOWN]),
                'unknown_volume': next((s['volume'] for s in services if s['service'] == UNKNOWN), 0)
            }
        except Exception:
            return {}
    
    async def _get_threat_intelligence(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze potential security threats"""
        failures = {"sum": {"field": "records.count"}}
        query = {
            "query": self._period_filter(customer_id, start_date, end_date),
            "aggs": {"records": {"nested": {"path": "records"}, "aggs": {"failed": {
                "filter": {"bool": {"must_not": {"term": {"records.dmarc_result": "pass"}}}},
                "aggs": {
                    "total": failures,
                    "source_count": {"cardinality": {"field": "records.source_ip"}},
                    "high_failure": {"terms": {"field": "records.source_ip", "size": 1000},
                                     "aggs": {"failures": failures,
                                              "over_100": {"bucket_selector": {
                                                  "buckets_path": {"n": "failures"}, "script": "params.n > 100"}}}},
                    "sources": {"terms": {"field": "records.source_ip", "size": 5, "order": {"failures": "desc"}},
                                "aggs": {"failures": failures}},
                }}}}},
        }
        
        try:
            result = es_service.search_documents("reports", query, size=0)
            failed = result["aggregations"]["records"]["failed"]
            return {
                'suspicious_sources': [{'ip': b["key"], 'failed_emails': int(b["failures"]["value"])}
                                       for b in failed["sources"]["buckets"]],
                'total_failed_sources': failed["source_count"]["value"],
                'threat_indicators': {
                    'high_failure_ips': len(failed["high_failure"]["buckets"]),
                    'authentication_bypass_attempts': int(failed["total"]["value"])
                }
            }
        except Exception:
            return {}
    
    async def _calculate_compliance_score(self, customer_id: str) -> Dict[str, Any]:
        """Calculate email authentication compliance score"""
        # This is a simplified compliance scoring system
        # In production, this would be based on industry standards
        
        try:
            # Get recent 7-day performance
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            metrics = await self._get_basic_metrics(customer_id, start_date, end_date)
            
            # No reports this week says nothing about how authentication is doing
            if not metrics.get('total_emails'):
                return {'overall_score': None, 'level': 'No recent reports', 'color': 'gray', 'recommendations': []}
            
            # Scoring criteria
            spf_score = min(metrics.get('spf_pass_rate', 0), 100) * 0.3
            dkim_score = min(metrics.get('dkim_pass_rate', 0), 100) * 0.3
            dmarc_score = min(metrics.get('dmarc_pass_rate', 0), 100) * 0.4
            
            total_score = spf_score + dkim_score + dmarc_score
            
            # Determine compliance level
            if total_score >= 95:
                level = "Excellent"
                color = "green"
            elif total_score >= 85:
                level = "Good"
                color = "blue"
            elif total_score >= 70:
                level = "Fair"
                color = "yellow"
            else:
                level = "Poor"
                color = "red"
            
            return {
                'overall_score': round(total_score, 1),
                'level': level,
                'color': color,
                'component_scores': {
                    'spf': round(spf_score / 0.3, 1),
                    'dkim': round(dkim_score / 0.3, 1),
                    'dmarc': round(dmarc_score / 0.4, 1)
                },
                'recommendations': self._get_compliance_recommendations(total_score, metrics)
            }
        except Exception:
            return {
                'overall_score': 0,
                'level': 'Unknown',
                'color': 'gray'
            }
    
    def _get_compliance_recommendations(self, score: float, metrics: Dict[str, Any]) -> List[str]:
        """Generate compliance improvement recommendations"""
        recommendations = []
        
        if metrics.get('spf_pass_rate', 0) < 95:
            recommendations.append("Improve SPF record configuration to increase pass rate")
        
        if metrics.get('dkim_pass_rate', 0) < 95:
            recommendations.append("Ensure all email services have proper DKIM signing")
        
        if metrics.get('dmarc_pass_rate', 0) < 95:
            recommendations.append("Review DMARC policy alignment and authentication setup")
        
        if score < 70:
            recommendations.append("Consider implementing stricter email authentication policies")
        
        return recommendations

analytics_service = AdvancedAnalyticsService()