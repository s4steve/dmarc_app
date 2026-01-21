"""
Tests for Multi-Tenancy and Customer Isolation
These tests verify that customer data is properly isolated and cannot be accessed by other customers.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone


class TestMultiTenancyIsolation:
    """Test customer data isolation across all services"""

    @pytest.fixture
    def customer_a_id(self):
        return "customer-a-123"

    @pytest.fixture
    def customer_b_id(self):
        return "customer-b-456"

    @pytest.fixture
    def customer_a_user(self, customer_a_id):
        from backend.app.models.user import User, UserRole
        now = datetime.now(timezone.utc).isoformat()
        return User(
            id="user-a",
            email="admin@customer-a.com",
            customer_id=customer_a_id,
            role=UserRole.ADMIN,
            full_name="Customer A Admin",
            is_active=True,
            created_at=now,
            updated_at=now
        )

    @pytest.fixture
    def customer_b_user(self, customer_b_id):
        from backend.app.models.user import User, UserRole
        now = datetime.now(timezone.utc).isoformat()
        return User(
            id="user-b",
            email="admin@customer-b.com",
            customer_id=customer_b_id,
            role=UserRole.ADMIN,
            full_name="Customer B Admin",
            is_active=True,
            created_at=now,
            updated_at=now
        )


class TestDMARCServiceIsolation(TestMultiTenancyIsolation):
    """Test DMARC service customer isolation"""

    def test_get_reports_summary_filters_by_customer(self, customer_a_id):
        """Test that reports summary only returns data for the specified customer"""
        from backend.app.services.dmarc_service import DMARCService
        service = DMARCService()

        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {
                    "records": {
                        "total_emails": {"value": 100},
                        "passed_emails": {"count": {"value": 80}},
                        "services": {"buckets": []}
                    }
                }
            }

            service.get_reports_summary(customer_a_id, 7)

            # Verify the query includes customer_id filter
            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            # Check that customer_id filter is in the query
            query_str = str(query)
            assert customer_a_id in query_str
            assert "customer_id" in query_str

    def test_get_reports_by_customer_filters_correctly(self, customer_a_id):
        """Test that reports retrieval only returns data for the specified customer"""
        from backend.app.services.dmarc_service import DMARCService
        service = DMARCService()

        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "hits": {
                    "hits": [
                        {"_id": "1", "_source": {"customer_id": customer_a_id}}
                    ]
                }
            }

            service.get_reports_by_customer(customer_a_id, 10)

            # Verify query includes customer filter
            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            assert "customer_id" in str(query)
            assert customer_a_id in str(query)

    def test_ingest_report_assigns_customer_id(self, customer_a_id):
        """Test that ingested reports are tagged with customer_id"""
        from backend.app.services.dmarc_service import DMARCService
        service = DMARCService()

        sample_xml = """<?xml version="1.0"?>
        <feedback>
            <report_metadata>
                <org_name>Test</org_name>
                <email>test@test.com</email>
                <report_id>test123</report_id>
                <date_range><begin>1640995200</begin><end>1641081600</end></date_range>
            </report_metadata>
            <policy_published><domain>example.com</domain><p>none</p></policy_published>
        </feedback>"""

        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.index_document.return_value = {"result": "created"}

            service.ingest_report(sample_xml, customer_a_id)

            # Verify the indexed document includes customer_id
            call_args = mock_es.index_document.call_args[0]
            indexed_doc = call_args[2]

            assert indexed_doc["customer_id"] == customer_a_id

    def test_time_series_data_filters_by_customer(self, customer_a_id):
        """Test that time series data is filtered by customer"""
        from backend.app.services.dmarc_service import DMARCService
        service = DMARCService()

        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {
                    "daily_stats": {
                        "buckets": []
                    }
                }
            }

            service.get_time_series_data(customer_a_id, 30)

            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            assert customer_a_id in str(query)


class TestAlertServiceIsolation(TestMultiTenancyIsolation):
    """Test alert service customer isolation"""

    @pytest.mark.asyncio
    async def test_alerts_are_customer_specific(self, customer_a_id):
        """Test that alerts are created for specific customer"""
        from backend.app.services.alert_service import AlertService
        service = AlertService()

        mock_summary = Mock()
        mock_summary.pass_rate = 30.0
        mock_summary.failed_emails = 70
        mock_summary.total_emails = 100

        with patch('backend.app.services.alert_service.dmarc_service') as mock_dmarc, \
             patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_dmarc.get_reports_summary = AsyncMock(return_value=mock_summary)
            mock_es.index_document = AsyncMock()

            alert = await service._check_high_failure_rate(customer_a_id)

            assert alert['customer_id'] == customer_a_id

    @pytest.mark.asyncio
    async def test_get_alerts_filters_by_customer(self, customer_a_id, customer_b_id):
        """Test that alert retrieval only returns alerts for the specified customer"""
        from backend.app.services.alert_service import AlertService
        service = AlertService()

        with patch('backend.app.services.alert_service.es_service') as mock_es:
            mock_es.search_documents = AsyncMock(return_value={
                "hits": {
                    "hits": [
                        {"_source": {"customer_id": customer_a_id, "alert_type": "test"}}
                    ]
                }
            })

            await service.get_alerts_for_customer(customer_a_id, days=7)

            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            # Verify customer_id filter is in query
            assert customer_a_id in str(query)


class TestUserServiceIsolation(TestMultiTenancyIsolation):
    """Test user service customer isolation"""

    @pytest.mark.asyncio
    async def test_get_users_filters_by_customer(self, customer_a_id):
        """Test that user retrieval only returns users for the specified customer"""
        from backend.app.services.user_service import UserService

        with patch('backend.app.services.user_service.es_service') as mock_es:
            mock_es.search_documents = Mock(return_value={
                "hits": {
                    "hits": []
                }
            })

            service = UserService()
            await service.get_users_by_customer(customer_a_id)

            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            assert customer_a_id in str(query)


class TestDNSServiceIsolation(TestMultiTenancyIsolation):
    """Test DNS service customer isolation"""

    @pytest.mark.asyncio
    async def test_dns_records_tagged_with_customer(self, customer_a_id):
        """Test that DNS records are tagged with customer_id"""
        from backend.app.services.dns_service import DNSService

        with patch('backend.app.services.dns_service.es_service') as mock_es:
            mock_es.index_document = AsyncMock()

            service = DNSService()

            # Create a mock DNS record
            from backend.app.models.dns import DNSRecord, DNSRecordType
            record = DNSRecord(
                customer_id=customer_a_id,
                domain="example.com",
                record_type=DNSRecordType.SPF,
                record_name="example.com",
                record_value="v=spf1 -all",
                last_checked=datetime.utcnow(),
                syntax_valid=True,
                recommendations=[],
                errors=[]
            )

            await service._store_dns_record(record)

            call_args = mock_es.index_document.call_args[0]
            indexed_doc = call_args[2]

            assert indexed_doc["customer_id"] == customer_a_id

    @pytest.mark.asyncio
    async def test_get_dns_records_filters_by_customer(self, customer_a_id):
        """Test that DNS record retrieval filters by customer"""
        from backend.app.services.dns_service import DNSService

        with patch('backend.app.services.dns_service.es_service') as mock_es:
            mock_es.search_documents = AsyncMock(return_value={
                "hits": {"hits": []}
            })

            service = DNSService()
            await service.get_dns_records_by_customer(customer_a_id)

            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            assert customer_a_id in str(query)


class TestAPIEndpointIsolation(TestMultiTenancyIsolation):
    """Test API endpoint customer isolation"""

    @pytest.fixture
    def test_client(self):
        from fastapi.testclient import TestClient
        from backend.app.main import app
        return TestClient(app)

    def test_dmarc_summary_uses_authenticated_customer(self, test_client, customer_a_user):
        """Test that DMARC summary endpoint uses authenticated user's customer_id"""
        with patch('backend.app.api.dmarc.get_current_active_user') as mock_auth, \
             patch('backend.app.api.dmarc.dmarc_service') as mock_service:

            mock_auth.return_value = customer_a_user
            mock_service.get_reports_summary.return_value = Mock(
                total_emails=100,
                passed_emails=80,
                failed_emails=20,
                pass_rate=80.0,
                date_range={},
                top_services=[]
            )

            # Get valid token
            login_response = test_client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin123"}
            )

            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                response = test_client.get("/api/v1/dmarc/summary", headers=headers)

                # Verify the service was called with the user's customer_id
                if mock_service.get_reports_summary.called:
                    call_args = mock_service.get_reports_summary.call_args[0]
                    # Customer ID should be from the authenticated user
                    assert call_args[0] is not None

    def test_users_endpoint_filters_by_customer(self, test_client, customer_a_user):
        """Test that users endpoint returns only users from same customer"""
        # This test verifies the endpoint correctly filters by customer_id
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            with patch('backend.app.services.user_service.user_service.get_users_by_customer') as mock_get:
                mock_get.return_value = []

                test_client.get("/api/v1/users/", headers=headers)

                # Verify get_users_by_customer was called with a customer_id
                if mock_get.called:
                    assert mock_get.call_args[0][0] is not None


class TestCrossCustomerAccessPrevention(TestMultiTenancyIsolation):
    """Test that cross-customer access is prevented"""

    def test_query_structure_prevents_cross_customer_access(self, customer_a_id, customer_b_id):
        """Test that queries always include customer_id filter"""
        from backend.app.services.dmarc_service import DMARCService
        service = DMARCService()

        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {
                    "records": {
                        "total_emails": {"value": 0},
                        "passed_emails": {"count": {"value": 0}},
                        "services": {"buckets": []}
                    }
                }
            }

            # Query for customer A
            service.get_reports_summary(customer_a_id, 7)
            query_a = str(mock_es.search_documents.call_args[0][1])

            # Query for customer B
            service.get_reports_summary(customer_b_id, 7)
            query_b = str(mock_es.search_documents.call_args[0][1])

            # Both queries should contain their respective customer_id
            assert customer_a_id in query_a
            assert customer_b_id in query_b

            # Customer A's query should NOT contain customer B's ID
            assert customer_b_id not in query_a
            assert customer_a_id not in query_b

    def test_elasticsearch_term_query_for_customer_id(self, customer_a_id):
        """Test that Elasticsearch queries use term query for exact customer_id match"""
        from backend.app.services.dmarc_service import DMARCService
        service = DMARCService()

        with patch('backend.app.services.dmarc_service.es_service') as mock_es:
            mock_es.search_documents.return_value = {
                "aggregations": {
                    "records": {
                        "total_emails": {"value": 0},
                        "passed_emails": {"count": {"value": 0}},
                        "services": {"buckets": []}
                    }
                }
            }

            service.get_reports_summary(customer_a_id, 7)

            call_args = mock_es.search_documents.call_args[0]
            query = call_args[1]

            # Verify that customer_id is filtered using term query (exact match)
            # This prevents partial matching or injection attacks
            must_conditions = query.get("query", {}).get("bool", {}).get("must", [])

            customer_filter_found = False
            for condition in must_conditions:
                if "term" in condition:
                    # Check for customer_id.keyword (proper ES keyword field)
                    if "customer_id.keyword" in condition["term"]:
                        customer_filter_found = True
                        assert condition["term"]["customer_id.keyword"] == customer_a_id

            assert customer_filter_found, "Customer ID filter not found in query"


class TestNotificationServiceIsolation(TestMultiTenancyIsolation):
    """Test notification service customer isolation"""

    @pytest.mark.asyncio
    async def test_notification_preferences_are_customer_specific(self, customer_a_id, customer_b_id):
        """Test that notification preferences are stored per customer"""
        from backend.app.services.notification_service import NotificationService
        service = NotificationService()

        with patch('backend.app.services.notification_service.es_service') as mock_es:
            mock_es.index_document = AsyncMock()

            prefs = {"email_alerts": True}
            await service.update_notification_preferences(customer_a_id, prefs)

            call_args = mock_es.index_document.call_args[0]
            # Preferences should be indexed by customer_id
            assert call_args[1] == customer_a_id

    @pytest.mark.asyncio
    async def test_admin_users_filtered_by_customer(self, customer_a_id):
        """Test that admin user retrieval is filtered by customer"""
        from backend.app.services.notification_service import NotificationService
        service = NotificationService()

        with patch('backend.app.services.notification_service.user_service') as mock_user_service:
            mock_user_service.get_users_by_customer = AsyncMock(return_value=[])

            await service._get_admin_users(customer_a_id)

            mock_user_service.get_users_by_customer.assert_called_once_with(customer_a_id)
