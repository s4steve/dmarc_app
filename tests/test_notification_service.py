"""
Tests for Notification Service functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestNotificationService:
    """Test notification service functionality"""

    @pytest.fixture
    def notification_service(self):
        from backend.app.services.notification_service import NotificationService
        return NotificationService()

    @pytest.fixture
    def sample_alert(self):
        return {
            'id': 'alert-123',
            'customer_id': 'test-customer',
            'alert_type': 'high_failure_rate',
            'severity': 'high',
            'title': 'High DMARC Failure Rate',
            'description': 'Failure rate exceeded threshold',
            'data': {
                'pass_rate': 40.0,
                'failed_emails': 60,
                'total_emails': 100
            },
            'created_at': datetime.utcnow().isoformat()
        }

    @pytest.fixture
    def sample_summary(self):
        return {
            'total_emails': 10000,
            'passed_emails': 8000,
            'failed_emails': 2000,
            'pass_rate': 80.0,
            'top_services': [
                {'service': 'Google Workspace', 'email_count': 5000},
                {'service': 'SendGrid', 'email_count': 3000}
            ]
        }

    @pytest.fixture
    def mock_admin_user(self):
        user = Mock()
        user.email = "admin@example.com"
        user.role = "admin"
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_send_alert_notification_success(self, notification_service, sample_alert, mock_admin_user):
        """Test successful alert notification sending"""
        with patch.object(notification_service, '_get_admin_users', new_callable=AsyncMock) as mock_get_admins, \
             patch.object(notification_service, '_send_email', new_callable=AsyncMock) as mock_send, \
             patch.object(notification_service, '_log_notification', new_callable=AsyncMock):

            mock_get_admins.return_value = [mock_admin_user]
            mock_send.return_value = True

            result = await notification_service.send_alert_notification("test-customer", sample_alert)

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert call_args[0] == "admin@example.com"
            assert "High DMARC Failure Rate" in call_args[1]

    @pytest.mark.asyncio
    async def test_send_alert_notification_no_admins(self, notification_service, sample_alert):
        """Test alert notification when no admins exist"""
        with patch.object(notification_service, '_get_admin_users', new_callable=AsyncMock) as mock_get_admins:
            mock_get_admins.return_value = []

            result = await notification_service.send_alert_notification("test-customer", sample_alert)

            assert result is False

    @pytest.mark.asyncio
    async def test_send_weekly_summary_success(self, notification_service, sample_summary, mock_admin_user):
        """Test successful weekly summary sending"""
        with patch.object(notification_service, '_get_admin_users', new_callable=AsyncMock) as mock_get_admins, \
             patch.object(notification_service, '_send_email', new_callable=AsyncMock) as mock_send:

            mock_get_admins.return_value = [mock_admin_user]
            mock_send.return_value = True

            result = await notification_service.send_weekly_summary("test-customer", sample_summary)

            assert result is True
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0]
            assert "Weekly DMARC Analytics Summary" in call_args[1]

    @pytest.mark.asyncio
    async def test_send_dns_change_notification(self, notification_service, mock_admin_user):
        """Test DNS change notification"""
        changes = [
            "SPF record changed",
            "DKIM record added"
        ]

        with patch.object(notification_service, '_get_admin_users', new_callable=AsyncMock) as mock_get_admins, \
             patch.object(notification_service, '_send_email', new_callable=AsyncMock) as mock_send:

            mock_get_admins.return_value = [mock_admin_user]
            mock_send.return_value = True

            result = await notification_service.send_dns_change_notification(
                "test-customer", "example.com", changes
            )

            assert result is True
            call_args = mock_send.call_args[0]
            assert "example.com" in call_args[1]

    @pytest.mark.asyncio
    async def test_get_admin_users_filters_correctly(self, notification_service):
        """Test that only active admins are returned"""
        admin_user = Mock()
        admin_user.role = "admin"
        admin_user.is_active = True

        readonly_user = Mock()
        readonly_user.role = "read_only"
        readonly_user.is_active = True

        inactive_admin = Mock()
        inactive_admin.role = "admin"
        inactive_admin.is_active = False

        system_admin = Mock()
        system_admin.role = "system_admin"
        system_admin.is_active = True

        with patch('backend.app.services.notification_service.user_service') as mock_user_service:
            mock_user_service.get_users_by_customer = AsyncMock(
                return_value=[admin_user, readonly_user, inactive_admin, system_admin]
            )

            admins = await notification_service._get_admin_users("test-customer")

            assert len(admins) == 2
            assert admin_user in admins
            assert system_admin in admins
            assert readonly_user not in admins
            assert inactive_admin not in admins

    def test_create_alert_email_body_high_severity(self, notification_service, sample_alert):
        """Test alert email body creation for high severity"""
        body = notification_service._create_alert_email_body(sample_alert)

        assert "High DMARC Failure Rate" in body
        assert "HIGH" in body
        assert "pass rate" in body.lower() or "Pass Rate" in body

    def test_create_alert_email_body_medium_severity(self, notification_service):
        """Test alert email body creation for medium severity"""
        alert = {
            'title': 'Volume Spike',
            'severity': 'medium',
            'description': 'Email volume increased',
            'data': {'volume': 1000},
            'created_at': datetime.utcnow().isoformat()
        }

        body = notification_service._create_alert_email_body(alert)

        assert "Volume Spike" in body
        assert "MEDIUM" in body

    def test_create_summary_email_body(self, notification_service, sample_summary):
        """Test weekly summary email body creation"""
        body = notification_service._create_summary_email_body(sample_summary)

        assert "10,000" in body  # total emails formatted
        assert "80.0%" in body or "80%" in body  # pass rate
        assert "Google Workspace" in body
        assert "SendGrid" in body

    def test_create_dns_change_email_body(self, notification_service):
        """Test DNS change email body creation"""
        changes = ["SPF record modified", "DKIM selector added"]

        body = notification_service._create_dns_change_email_body("example.com", changes)

        assert "example.com" in body
        assert "SPF record modified" in body
        assert "DKIM selector added" in body

    def test_convert_to_html(self, notification_service):
        """Test plain text to HTML conversion"""
        text = "Line 1\nLine 2\nLine 3"

        html = notification_service._convert_to_html(text)

        assert "<html>" in html
        assert "<br>" in html
        assert "Line 1" in html

    @pytest.mark.asyncio
    async def test_send_email_mock_mode(self, notification_service):
        """Test email sending in mock mode (localhost without credentials)"""
        notification_service.smtp_server = "localhost"
        notification_service.smtp_username = None

        result = await notification_service._send_email(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )

        # In mock mode, should return True without actually sending
        assert result is True

    @pytest.mark.asyncio
    async def test_log_notification(self, notification_service, mock_admin_user):
        """Test notification logging"""
        with patch('backend.app.services.notification_service.es_service') as mock_es:
            mock_es.index_document = AsyncMock()

            await notification_service._log_notification(
                "test-customer",
                "alert-123",
                "email",
                [mock_admin_user]
            )

            mock_es.index_document.assert_called_once()
            call_args = mock_es.index_document.call_args[0]
            assert call_args[0] == "notifications"
            log_entry = call_args[2]
            assert log_entry['customer_id'] == "test-customer"
            assert log_entry['alert_id'] == "alert-123"
            assert log_entry['notification_type'] == "email"
            assert log_entry['status'] == "sent"

    @pytest.mark.asyncio
    async def test_get_notification_preferences(self, notification_service):
        """Test retrieving notification preferences"""
        prefs = await notification_service.get_notification_preferences("test-customer")

        assert 'email_alerts' in prefs
        assert 'weekly_summary' in prefs
        assert 'dns_change_alerts' in prefs
        assert prefs['email_alerts'] is True

    @pytest.mark.asyncio
    async def test_update_notification_preferences_success(self, notification_service):
        """Test updating notification preferences"""
        new_prefs = {
            'email_alerts': False,
            'weekly_summary': True,
            'high_severity_only': True
        }

        with patch('backend.app.services.notification_service.es_service') as mock_es:
            mock_es.index_document = AsyncMock()

            result = await notification_service.update_notification_preferences(
                "test-customer", new_prefs
            )

            assert result is True
            mock_es.index_document.assert_called_once_with(
                "notification_preferences",
                "test-customer",
                new_prefs
            )

    @pytest.mark.asyncio
    async def test_update_notification_preferences_failure(self, notification_service):
        """Test notification preference update failure handling"""
        with patch('backend.app.services.notification_service.es_service') as mock_es:
            mock_es.index_document = AsyncMock(side_effect=Exception("ES error"))

            result = await notification_service.update_notification_preferences(
                "test-customer", {}
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_to_multiple_admins(self, notification_service, sample_alert):
        """Test sending alerts to multiple admin users"""
        admin1 = Mock()
        admin1.email = "admin1@example.com"
        admin1.role = "admin"
        admin1.is_active = True

        admin2 = Mock()
        admin2.email = "admin2@example.com"
        admin2.role = "system_admin"
        admin2.is_active = True

        with patch.object(notification_service, '_get_admin_users', new_callable=AsyncMock) as mock_get_admins, \
             patch.object(notification_service, '_send_email', new_callable=AsyncMock) as mock_send, \
             patch.object(notification_service, '_log_notification', new_callable=AsyncMock):

            mock_get_admins.return_value = [admin1, admin2]
            mock_send.return_value = True

            result = await notification_service.send_alert_notification("test-customer", sample_alert)

            assert result is True
            assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_in_send_alert(self, notification_service, sample_alert, mock_admin_user):
        """Test error handling when sending alert fails"""
        with patch.object(notification_service, '_get_admin_users', new_callable=AsyncMock) as mock_get_admins, \
             patch.object(notification_service, '_send_email', new_callable=AsyncMock) as mock_send:

            mock_get_admins.return_value = [mock_admin_user]
            mock_send.side_effect = Exception("SMTP error")

            result = await notification_service.send_alert_notification("test-customer", sample_alert)

            assert result is False
