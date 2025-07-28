from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..services.elasticsearch import es_service
import json

class AdvancedAnalyticsService:
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
            result = await es_service.search_documents("reports", query)
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
            result = await es_service.search_documents("reports", query)
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
            if len(trends) >= 2:
                recent_volume = sum(t['volume'] for t in trends[-7:]) / 7
                previous_volume = sum(t['volume'] for t in trends[-14:-7]) / 7
                volume_growth = ((recent_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
            else:
                volume_growth = 0
            
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
                "services": {
                    "terms": {
                        "script": {
                            "source": """
                            params._source.records.stream()
                                .map(record -> record.third_party_service != null ? record.third_party_service : 'Unknown')
                                .collect(Collectors.toList())
                            """
                        },
                        "size": 20
                    },
                    "aggs": {
                        "service_volume": {
                            "sum": {
                                "script": {
                                    "source": """
                                    params._source.records.stream()
                                        .filter(record -> {
                                            String service = record.third_party_service != null ? record.third_party_service : 'Unknown';
                                            return service.equals(params.service);
                                        })
                                        .mapToInt(record -> record.count).sum()
                                    """,
                                    "params": {"service": ""}
                                }
                            }
                        },
                        "service_pass": {
                            "sum": {
                                "script": {
                                    "source": """
                                    params._source.records.stream()
                                        .filter(record -> {
                                            String service = record.third_party_service != null ? record.third_party_service : 'Unknown';
                                            return service.equals(params.service) && record.dmarc_result.equals('pass');
                                        })
                                        .mapToInt(record -> record.count).sum()
                                    """,
                                    "params": {"service": ""}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            result = await es_service.search_documents("reports", query)
            service_buckets = result.get("aggregations", {}).get("services", {}).get("buckets", [])
            
            services = []
            for bucket in service_buckets:
                service_name = bucket["key"]
                volume = int(bucket["service_volume"]["value"])
                passed = int(bucket["service_pass"]["value"])
                
                services.append({
                    'service': service_name,
                    'volume': volume,
                    'pass_rate': (passed / volume * 100) if volume > 0 else 0,
                    'failed_emails': volume - passed
                })
            
            return {
                'services': sorted(services, key=lambda x: x['volume'], reverse=True),
                'total_services': len([s for s in services if s['service'] != 'Unknown']),
                'unknown_volume': next((s['volume'] for s in services if s['service'] == 'Unknown'), 0)
            }
        except Exception:
            return {}
    
    async def _get_threat_intelligence(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze potential security threats"""
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
                "failed_sources": {
                    "terms": {
                        "script": {
                            "source": """
                            params._source.records.stream()
                                .filter(record -> !record.dmarc_result.equals('pass'))
                                .map(record -> record.source_ip)
                                .collect(Collectors.toList())
                            """
                        },
                        "size": 10
                    },
                    "aggs": {
                        "failure_count": {
                            "sum": {
                                "script": {
                                    "source": """
                                    params._source.records.stream()
                                        .filter(record -> record.source_ip.equals(params.ip) && !record.dmarc_result.equals('pass'))
                                        .mapToInt(record -> record.count).sum()
                                    """,
                                    "params": {"ip": ""}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            result = await es_service.search_documents("reports", query)
            failed_sources = result.get("aggregations", {}).get("failed_sources", {}).get("buckets", [])
            
            suspicious_sources = []
            for bucket in failed_sources[:5]:  # Top 5 suspicious sources
                suspicious_sources.append({
                    'ip': bucket["key"],
                    'failed_emails': int(bucket["failure_count"]["value"])
                })
            
            return {
                'suspicious_sources': suspicious_sources,
                'total_failed_sources': len(failed_sources),
                'threat_indicators': {
                    'high_failure_ips': len([s for s in failed_sources if s["failure_count"]["value"] > 100]),
                    'authentication_bypass_attempts': sum(s["failure_count"]["value"] for s in failed_sources)
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