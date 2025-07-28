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
- **Elasticsearch**: Clustered search and analytics

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DMARCApp
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Start the frontend development server**
   ```bash
   npm start
   ```

### Access Points
- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Elasticsearch**: http://localhost:9200

## Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Security
SECRET_KEY=your-secret-key-here
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure-password

# Database
ELASTICSEARCH_URL=http://localhost:9200

# Email Notifications (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=alerts@yourdomain.com
```

### Default Credentials
- **Email**: admin@example.com
- **Password**: admin123

## API Documentation

The platform provides comprehensive API documentation through FastAPI's automatic OpenAPI generation:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/users/me` - Get current user profile

#### DMARC Analytics
- `GET /api/v1/dmarc/summary` - Get report summary with metrics
- `GET /api/v1/dmarc/time-series` - Historical trend data
- `POST /api/v1/dmarc/upload-report` - Upload XML reports

#### DNS Management
- `POST /api/v1/dns/check/{domain}` - Validate DNS records
- `GET /api/v1/dns/records` - Get customer DNS records

#### Alerts & Notifications
- `GET /api/v1/alerts/` - Retrieve security alerts
- `POST /api/v1/alerts/check` - Trigger alert checks
- `POST /api/v1/notifications/test-alert` - Send test notification

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
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

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