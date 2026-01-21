"""
Tests for Alert Service functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid


class TestAlertService:
    """Test alert service functionality"""

    @pytest.fixture
    def alert_service(self):
        from backend.app.services.alert_service import AlertService
        return AlertService()

    @pytest.fixture
    def mock_summary_high_failure(self):
        """Mock summary with high failure rate (>50%)"""
        mock = Mock()
        mock.pass_rate = 40.0  # 60% failure rate
        mock.failed_emails = 60
        mock.total_emails = 100
        return mock

    @pytest.fixture
    def mock_summary_normal(self):
        """Mock summary with normal failure rate"""
        mock = Mock()
        mock.pass_rate = 90.0
        mock.failed_emails = 10
        mock.total_emails = 100
        return mock

    @pytest.mark.asyncio
    async def test_check_high_failure_rate_triggers_alert(self, alert_service, mock_summary_high_failure):
        """Test that high failure rate triggers an alert"""
        with patch('backend.app.services.alert_service.dmarc_service') as mock_dmarc:
            mock_dmarc.get_reports_summary = AsyncMock(return_value=mock_summary_high_failure)

            alert = await alert_service._check_high_failure_rate("test-customer")

            assert alert is not None
            assert alert['alert_type'] == 'high_failure_rate'
            assert alert['severity'] == 'high'
            assert alert['customer_id'] == 'test-customer'
            assert 'pass_rate' in alert['data']

    @pytest.mark.asyncio
    async def test_check_high_failure_rate_no_alert_when_normal(self, alert_service, mock_summary_normal):
        """Test that normal failure rate does not trigger alert"""
        with patch('backend.app.services.alert_service.dmarc_service') as mock_dmarc:
            mock_dmarc.get_reports_summary = AsyncMock(return_value=mock_summary_normal)

            alert = await alert_service._check_high_failure_rate("test-customer")

            assert alert is None

    @pytest.mark.asyncio
    async def test_check_volume_spike_triggers_alert(self, alert_service):
        """Test that volume spike triggers an alert"""
        today_summary = Mock()
        today_summary.total_emails = 500

        week_summary = Mock()
        week_summary.total_emails = 700  # avg = 100/day, today = 500 (5x spike)

        with patch('backend.app.services.alert_service.dmarc_service') as mock_dmarc:
            mock_dmarc.get_reports_summary = AsyncMock(side_effect=[today_summary, week_summary])

            alert = await alert_service._check_volume_spike("test-customer")

            assert alert is not None
            assert alert['alert_type'] == 'volume_spike'
            assert alert['severity'] == 'medium'

    @pytest.mark.asyncio
    async def test_check_volume_spike_no_alert_when_normal(self, alert_service):
        """Test that normal volume does not trigger alert"""
        today_summary = Mock()
        today_summary.total_emails = 100

        week_summary = Mock()
        week_summary.total_emails = 700  # avg = 100/day

        with patch('backend.app.services.alert_service.dmarc_service') as mock_dmarc:
            mock_dmarc.get_reports_summary = AsyncMock(side_effect=[today_summary, week_summary])

            alert = await alert_service._check_volume_spike("test-customer")

            assert alert is None

    @pytest.mark.asyncio
    async def test_check_unknown_senders_triggers_alert(self, alert_service):
        """Test that unknown senders triggers an alert"""
        mock_es_response = {
            "aggregations": {
                "unknown_senders": {
                    "filter_unknown": {
                        "total_emails": {
                            "value": 50
                        }
                    }
                }
            }
        }

        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.search_documents = AsyncMock(return_value=mock_es_response)

            alert = await alert_service._check_unknown_senders("test-customer")

            assert alert is not None
            assert alert['alert_type'] == 'unknown_senders'
            assert alert['data']['unknown_email_count'] == 50

    @pytest.mark.asyncio
    async def test_check_unknown_senders_no_alert_when_below_threshold(self, alert_service):
        """Test that low unknown senders does not trigger alert"""
        mock_es_response = {
            "aggregations": {
                "unknown_senders": {
                    "filter_unknown": {
                        "total_emails": {
                            "value": 5
                        }
                    }
                }
            }
        }

        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.search_documents = AsyncMock(return_value=mock_es_response)

            alert = await alert_service._check_unknown_senders("test-customer")

            assert alert is None

    @pytest.mark.asyncio
    async def test_check_alerts_for_customer_combines_all_checks(self, alert_service):
        """Test that check_alerts_for_customer runs all checks"""
        with patch.object(alert_service, '_check_high_failure_rate', new_callable=AsyncMock) as mock_failure, \
             patch.object(alert_service, '_check_volume_spike', new_callable=AsyncMock) as mock_volume, \
             patch.object(alert_service, '_check_unknown_senders', new_callable=AsyncMock) as mock_unknown, \
             patch.object(alert_service, '_check_geographic_anomalies', new_callable=AsyncMock) as mock_geo, \
             patch.object(alert_service, '_store_alert', new_callable=AsyncMock):

            mock_failure.return_value = {'id': '1', 'alert_type': 'high_failure_rate'}
            mock_volume.return_value = None
            mock_unknown.return_value = {'id': '2', 'alert_type': 'unknown_senders'}
            mock_geo.return_value = None

            alerts = await alert_service.check_alerts_for_customer("test-customer")

            assert len(alerts) == 2
            mock_failure.assert_called_once_with("test-customer")
            mock_volume.assert_called_once_with("test-customer")
            mock_unknown.assert_called_once_with("test-customer")
            mock_geo.assert_called_once_with("test-customer")

    @pytest.mark.asyncio
    async def test_store_alert(self, alert_service):
        """Test alert storage in Elasticsearch"""
        alert = {
            'id': str(uuid.uuid4()),
            'customer_id': 'test-customer',
            'alert_type': 'test_alert',
            'severity': 'high'
        }

        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.index_document = AsyncMock()

            await alert_service._store_alert(alert)

            mock_es.index_document.assert_called_once_with("alerts", alert['id'], alert)

    @pytest.mark.asyncio
    async def test_get_alerts_for_customer(self, alert_service):
        """Test retrieving alerts for customer"""
        mock_es_response = {
            "hits": {
                "hits": [
                    {"_source": {"id": "1", "alert_type": "high_failure_rate"}},
                    {"_source": {"id": "2", "alert_type": "volume_spike"}}
                ]
            }
        }

        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.search_documents = AsyncMock(return_value=mock_es_response)

            alerts = await alert_service.get_alerts_for_customer("test-customer", days=7)

            assert len(alerts) == 2
            assert alerts[0]['alert_type'] == 'high_failure_rate'

    @pytest.mark.asyncio
    async def test_resolve_alert_success(self, alert_service):
        """Test resolving an alert"""
        mock_alert = {
            "_source": {
                "id": "alert-123",
                "alert_type": "high_failure_rate",
                "resolved": False
            }
        }

        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.get_document = AsyncMock(return_value=mock_alert)
            mock_es.index_document = AsyncMock()

            result = await alert_service.resolve_alert("alert-123")

            assert result is True
            # Verify the alert was updated with resolved status
            call_args = mock_es.index_document.call_args
            updated_alert = call_args[0][2]
            assert updated_alert['resolved'] is True
            assert 'resolved_at' in updated_alert

    @pytest.mark.asyncio
    async def test_resolve_alert_not_found(self, alert_service):
        """Test resolving non-existent alert"""
        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.get_document = AsyncMock(return_value=None)

            result = await alert_service.resolve_alert("nonexistent-alert")

            assert result is False

    def test_alert_thresholds_configuration(self, alert_service):
        """Test that alert thresholds are properly configured"""
        assert 'high_failure_rate' in alert_service.alert_thresholds
        assert 'volume_spike' in alert_service.alert_thresholds
        assert 'unknown_sender_threshold' in alert_service.alert_thresholds
        assert alert_service.alert_thresholds['high_failure_rate'] == 50.0
        assert alert_service.alert_thresholds['volume_spike'] == 2.0

    @pytest.mark.asyncio
    async def test_geographic_anomalies_returns_none(self, alert_service):
        """Test that geographic anomalies returns None (not implemented)"""
        result = await alert_service._check_geographic_anomalies("test-customer")
        assert result is None

    @pytest.mark.asyncio
    async def test_error_handling_in_failure_rate_check(self, alert_service):
        """Test error handling when failure rate check fails"""
        with patch('backend.app.services.alert_service.dmarc_service') as mock_dmarc:
            mock_dmarc.get_reports_summary = AsyncMock(side_effect=Exception("ES error"))

            alert = await alert_service._check_high_failure_rate("test-customer")

            # Should return None instead of raising exception
            assert alert is None

    @pytest.mark.asyncio
    async def test_run_periodic_checks(self, alert_service):
        """Test running periodic checks for all customers"""
        mock_es_response = {
            "aggregations": {
                "customers": {
                    "buckets": [
                        {"key": "customer-1"},
                        {"key": "customer-2"}
                    ]
                }
            }
        }

        with patch('backend.app.services.alert_service.es_service') as mock_es, \
             patch.object(alert_service, 'check_alerts_for_customer', new_callable=AsyncMock) as mock_check:
            mock_es.search_documents = AsyncMock(return_value=mock_es_response)
            mock_check.return_value = []

            await alert_service.run_periodic_checks()

            assert mock_check.call_count == 2
            mock_check.assert_any_call("customer-1")
            mock_check.assert_any_call("customer-2")
