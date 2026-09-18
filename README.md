# DMARC Analytics Platform

A comprehensive SaaS solution for monitoring, analyzing, and improving email authentication posture for small and medium businesses.

## Features

### 🔐 Email Authentication Monitoring
- **DMARC Report Processing**: Automated ingestion and analysis of XML aggregate reports
- **SPF/DKIM/DMARC Validation**: Real-time DNS record monitoring and syntax validation
- **Multi-Provider Support**: Compatible with reports from all major email providers

### 📊 Advanced Analytics
- **Interactive Dashboards**: Real-time metrics with customizable time ranges
- **Trend Analysis**: Historical data visualization with Recharts
- **Service Breakdown**: Automatic identification of third-party email services
- **Compliance Scoring**: Industry-standard email authentication scoring

### 🚨 Security Alerting
- **Threat Detection**: Automated alerts for suspicious email activity
- **Email Notifications**: Real-time alerts via email for security events
- **Failure Rate Monitoring**: Configurable thresholds for authentication failures
- **Volume Spike Detection**: Anomaly detection for unusual email patterns

### 🛠️ Configuration Management
- **Service Setup Guides**: Step-by-step instructions for popular email services
- **DNS Record Assistance**: Automated recommendations for SPF/DKIM/DMARC records
- **Validation Tools**: Built-in DNS syntax checker and troubleshooting

### 👥 Multi-Tenant Architecture
- **Customer Isolation**: Complete data separation between organizations
- **Role-Based Access**: Admin, read-only, and system admin permissions
- **User Management**: Team member invitation and access control

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Elasticsearch**: High-performance search and analytics engine
- **JWT Authentication**: Secure token-based authentication
- **Pydantic**: Data validation and serialization

### Frontend
- **React 18**: Modern React with TypeScript
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Responsive chart library
- **Heroicons**: Beautiful SVG icons

### Infrastructure
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Elasticsearch 8.11**: High-performance search and analytics engine
- **Redis 7**: Session management and caching

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/s4steve/dmarc_app.git
   cd dmarc_app
   ```

2. **Create `.env`** from the template and fill in every required value
   ```bash
   cp .env.example .env
   # generate each secret with: openssl rand -hex 32
   ```

3. **Build and start the services**
   ```bash
   docker compose build
   docker compose up -d
   ```
   For live code reload during development, add the dev override:
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`

4. **Verify services are running**
   ```bash
   docker compose ps
   ```

### For Development (without Docker)

1. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   npm start
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements-dev.txt
   uvicorn app.main:app --reload
   ```

### Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Elasticsearch**: http://localhost:9200 (loopback only)

## Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Required secrets (openssl rand -hex 32)
SECRET_KEY=
ELASTICSEARCH_PASSWORD=
REDIS_PASSWORD=

# First system admin: created on startup only when no users exist (password 12-72 chars)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=

# Database
ELASTICSEARCH_URL=http://localhost:9200

# Email Notifications (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=alerts@yourdomain.com
```

### First Login
There are no default credentials. On first start, the API creates a system admin from
`ADMIN_EMAIL` / `ADMIN_PASSWORD` if the users index is empty. Log in with those, then create
other users from the Users tab.

## API Documentation

The platform provides comprehensive API documentation through FastAPI's automatic OpenAPI generation:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Conventions

- **Base URL:** `http://localhost:8000/api/v1`. All paths below are relative to it.
- **Authentication:** get a token from `POST /auth/login` and send it as `Authorization: Bearer <token>`. Tokens expire after 30 minutes. `POST /auth/logout` revokes a token immediately.
- **Roles:**

  | Role | Can do |
  |---|---|
  | `read_only` | Read data for their own customer (the **user** level in the tables below) |
  | `admin` | Everything a user can, plus manage users, notifications and the DNS scanner for their own customer |
  | `system_admin` | Everything, across all customers, including the third-party service catalog shared by every customer |

- **Tenancy:** data is always scoped to the caller's `customer_id`, which comes from their user record. There's no way to query another customer's data by passing an ID.
- **Errors:** JSON with `detail` (and `message`) fields, e.g. `{"detail": "Not enough permissions", ...}`. Unexpected 500s return a generic message; details go to the server log only.
- **Common status codes:** `401` missing, invalid, expired or revoked token · `403` role too low · `404` not found (also returned for another customer's resources) · `413` payload too large · `422` request validation failed · `429` rate limited (see the `Retry-After` header).

### Quick example

```bash
API=http://localhost:8000/api/v1

# Log in
TOKEN=$(curl -s -X POST $API/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"<your password>"}' | jq -r .access_token)

# Upload a report, then read the summary for the last 30 days
curl -H "Authorization: Bearer $TOKEN" -F "file=@report.xml.gz" $API/dmarc/upload-report
curl -H "Authorization: Bearer $TOKEN" "$API/dmarc/summary?days=30"

# Log out (revokes the token)
curl -X POST -H "Authorization: Bearer $TOKEN" $API/auth/logout
```

### Endpoint reference

**Auth** in the tables below is the minimum role needed: **public** (no token), **user** (any logged-in user), **admin**, or **system_admin**.

#### Authentication — `/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | public | Body `{"email", "password"}`. Returns `{"access_token", "token_type": "bearer"}`. Rate limited to 5/min per IP. |
| POST | `/auth/logout` | user | Revokes the token used for this request. 10/min. |
| POST | `/auth/logout-all` | user | Revokes every active session for the current user. 5/min. |
| GET | `/auth/sessions` | user | Lists the caller's active sessions (`created_at`, `last_accessed`, `ip_address`, `user_agent`). 20/min. |

#### Users — `/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/users/me` | user | The current user's profile. |
| GET | `/users/` | admin | Users in the caller's customer (all users for a `system_admin`). |
| POST | `/users/` | admin | Create a user. Body: `email`, `password` (12-72 chars), `customer_id`, `role` (`read_only` default, `admin`, `system_admin`), `full_name`, `is_active`. A tenant admin always creates users in their own customer and can't assign `system_admin`. |
| PUT | `/users/{user_id}` | admin | Partial update: `email`, `full_name`, `role`, `is_active`. Setting `is_active: false` cuts off the user's existing tokens immediately. Tenant admins can't touch `system_admin` accounts or grant that role. |
| DELETE | `/users/{user_id}` | admin | Delete a user. You can't delete yourself. |

#### DMARC reports — `/dmarc`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/dmarc/upload-report` | user | Multipart upload, field `file`, a `.xml` or `.xml.gz` aggregate report. Max 10 MB uploaded / 50 MB decompressed. Documents with a `DOCTYPE` are rejected. Returns `{"message", "report_id"}`. 5/min per session. |
| GET | `/dmarc/summary` | user | Totals, pass/fail counts, `pass_rate` and top sending services. Query: `days` (1-365, default 7), `domain` (optional). 30/min per session. |
| GET | `/dmarc/reports` | user | Raw reports, newest first. Query: `limit` (1-1000, default 100), `domain`. |
| GET | `/dmarc/time-series` | user | Daily totals and pass rate. Query: `days` (1-365, default 30), `domain`. |

#### Analytics — `/analytics`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/analytics/detailed-report` | user | Detailed metrics for the period. Query: `days` (1-365, default 30). |
| GET | `/analytics/export/{format}` | user | `format` is `json`, `csv` or `pdf`. Query: `days`. **Only `json` works at the moment**; `csv` and `pdf` return 500 because the export functions aren't implemented yet. |

#### Domains — `/domains`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/domains/` | user | The customer's monitored domains. |
| POST | `/domains/` | user | Body `{"name": "example.com"}`. The name must be a valid DNS name. |
| DELETE | `/domains/{domain_id}` | user | Remove a domain. |

> Domains are currently held in memory, so they're lost when the API restarts.

#### DNS — `/dns` and `/dns-scanner`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/dns/check/{domain}` | user | Looks up and validates SPF, DMARC, DKIM and MX records, stores the results, and returns them with an `overall_status` and recommendations. |
| GET | `/dns/records` | user | Previously checked DNS records for the customer. |
| POST | `/dns-scanner/scan-domain/` | admin | Body `{"domain": "example.com"}`. Returns the live DMARC, SPF and DKIM (`_dkim` selector) records. |

#### Alerts — `/alerts`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/alerts/` | user | Alerts for the customer. Query: `days` (1-30, default 7). |
| POST | `/alerts/check` | user | Runs the alert checks now (high failure rate, volume spike, unknown senders) and returns any new alerts. |
| POST | `/alerts/{alert_id}/resolve` | user | Marks an alert resolved. Returns 404 for alerts that belong to another customer. |

#### Notifications — `/notifications`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/notifications/preferences` | admin | The customer's notification settings. |
| PUT | `/notifications/preferences` | admin | Body: `email_alerts`, `weekly_summary`, `dns_change_alerts`, `high_severity_only` (booleans) and `alert_threshold: {"failure_rate": 0-100, "volume_spike": >0}`. Unknown fields are rejected. |
| POST | `/notifications/test-alert` | admin | Emails a test alert to the customer's admins. |

#### Configuration guidance — `/configuration`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/configuration/services` | user | Setup instructions for every supported email service. |
| GET | `/configuration/services/{service_name}` | user | Instructions for one service. 404 if it's unknown. |
| GET | `/configuration/guidance/spf` | user | General SPF guidance. |
| GET | `/configuration/guidance/dmarc` | user | DMARC policy guidance. |
| GET | `/configuration/guidance/dkim` | user | DKIM guidance. |

#### Third-party services — `/services`

The catalog of known sending services (used to label report sources) is shared by all customers, so only a `system_admin` can change it.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/services/` | user | All active services. |
| POST | `/services/` | system_admin | Add a service. Body: `service_name`, `ip_ranges`, `domain_patterns`, `reverse_dns_patterns` (lists), plus optional `configuration_instructions`, `documentation`, `setup_guide`, `troubleshooting`, `is_active`. |
| POST | `/services/initialize` | system_admin | Load the built-in default services. |
| GET | `/services/admin` | system_admin | All services, with full details. |
| GET | `/services/admin/{service_id}` | system_admin | One service. |
| PUT | `/services/admin/{service_id}` | system_admin | Partial update of the fields listed for `POST /services/`. |
| DELETE | `/services/admin/{service_id}` | system_admin | Delete a service. |
| POST | `/services/admin/{service_id}/documentation` | system_admin | Body: `service_id`, `documentation`, optional `setup_guide` and `troubleshooting`. The path ID is the one that's updated. |
| POST | `/services/admin/recreate-index` | system_admin | **Destructive:** drops and rebuilds the services index, then reloads the defaults. Custom services are lost. |

#### Health checks (public)

`GET /health` (at the server root, not under `/api/v1`), plus `GET /dmarc/health`, `/dns/health`, `/alerts/health`, `/configuration/health`, `/notifications/health` and `/analytics/health`. Each returns `{"status": "healthy", ...}`.

## Usage Guide

### 1. Initial Setup
1. Log in with the default admin credentials
2. Initialize third-party service identification: `POST /api/v1/services/initialize`
3. Configure notification preferences in the dashboard

### 2. Upload DMARC Reports
- Use the Upload tab in the dashboard
- Drag and drop XML files from email providers
- Monitor processing status and results

### 3. Monitor Dashboard
- View real-time authentication metrics
- Analyze trends over different time periods
- Identify top email services and their performance

### 4. Configure DNS Records
- Use the DNS Records tab to check current configuration
- Follow recommendations for SPF/DKIM/DMARC improvements
- Copy suggested DNS records to your DNS provider

### 5. Manage Alerts
- Review security alerts in the Alerts tab
- Configure notification preferences
- Resolve alerts after investigation

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Testing

The project includes comprehensive test suites for both functional and security testing.

```bash
# Run all backend tests
PYTHONPATH=. pytest tests/ -v

# Run specific test categories
pytest tests/test_alert_service.py -v      # Alert service tests
pytest tests/test_dns_service.py -v        # DNS validation tests
pytest tests/test_multi_tenancy.py -v      # Customer isolation tests
pytest tests/test_security_comprehensive.py -v  # Security tests

# Frontend tests
cd frontend
npm test
```

#### Test Coverage
- **Alert Service**: Failure rate detection, volume spikes, unknown senders
- **Notification Service**: Email notifications, admin filtering, preferences
- **DNS Service**: SPF/DKIM/DMARC validation, recommendations engine
- **Multi-tenancy**: Customer data isolation across all services
- **Security**: Authentication, input validation, cryptographic security

## Deployment

### Production Deployment
1. Update environment variables for production
2. Configure proper SSL certificates
3. Set up email SMTP for notifications
4. Scale Elasticsearch cluster for production load

### Security Considerations
- Change default admin credentials
- Use strong SECRET_KEY
- Configure CORS origins appropriately
- Set up proper firewall rules
- Enable Elasticsearch authentication in production

## Monitoring

The platform includes comprehensive monitoring capabilities:

- **Application Health**: `/health` endpoints for all services
- **Elasticsearch Metrics**: Index performance and cluster health
- **Alert System**: Automated monitoring of authentication failures
- **Audit Logging**: Complete audit trail of user actions

## Support

### Documentation
- **Configuration Guide**: Built-in step-by-step setup instructions
- **Service Integration**: Detailed guides for popular email services
- **DNS Setup**: Automated recommendations and validation

### Troubleshooting
- Check service health endpoints
- Review Elasticsearch logs for data processing issues
- Verify DNS record syntax using built-in validator
- Test email notifications with test alert feature

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Submit a pull request with detailed description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

### Future Enhancements
- **API Access**: Third-party integrations and webhook support
- **Advanced ML**: Machine learning for threat detection
- **Mobile App**: iOS and Android applications
- **SAML/OAuth**: Enterprise authentication integration
- **Real-time Streaming**: Live data processing and alerts

---

Built with ❤️ for better email security