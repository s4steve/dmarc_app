import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.config import settings
from ..services.user_service import user_service
from .elasticsearch import es_service
import uuid

class NotificationService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER if hasattr(settings, 'SMTP_SERVER') else "localhost"
        self.smtp_port = settings.SMTP_PORT if hasattr(settings, 'SMTP_PORT') else 587
        self.smtp_username = settings.SMTP_USERNAME if hasattr(settings, 'SMTP_USERNAME') else None
        self.smtp_password = settings.SMTP_PASSWORD if hasattr(settings, 'SMTP_PASSWORD') else None
        self.from_email = settings.FROM_EMAIL if hasattr(settings, 'FROM_EMAIL') else "alerts@dmarcanalytics.com"
    
    async def send_alert_notification(self, customer_id: str, alert: Dict[str, Any]) -> bool:
        """Send email notification for security alerts"""
        try:
            # Get admin users for the customer
            admin_users = await self._get_admin_users(customer_id)
            if not admin_users:
                return False
            
            # Create email content
            subject = f"DMARC Alert: {alert['title']}"
            body = self._create_alert_email_body(alert)
            
            # Send to all admin users
            for user in admin_users:
                await self._send_email(user.email, subject, body)
            
            # Log notification
            await self._log_notification(customer_id, alert['id'], 'email', admin_users)
            
            return True
        except Exception as e:
            print(f"Failed to send alert notification: {e}")
            return False
    
    async def send_weekly_summary(self, customer_id: str, summary_data: Dict[str, Any]) -> bool:
        """Send weekly DMARC summary email"""
        try:
            admin_users = await self._get_admin_users(customer_id)
            if not admin_users:
                return False
            
            subject = "Weekly DMARC Analytics Summary"
            body = self._create_summary_email_body(summary_data)
            
            for user in admin_users:
                await self._send_email(user.email, subject, body)
            
            return True
        except Exception as e:
            print(f"Failed to send weekly summary: {e}")
            return False
    
    async def send_dns_change_notification(self, customer_id: str, domain: str, changes: List[str]) -> bool:
        """Send notification when DNS records change"""
        try:
            admin_users = await self._get_admin_users(customer_id)
            if not admin_users:
                return False
            
            subject = f"DNS Changes Detected for {domain}"
            body = self._create_dns_change_email_body(domain, changes)
            
            for user in admin_users:
                await self._send_email(user.email, subject, body)
            
            return True
        except Exception as e:
            print(f"Failed to send DNS change notification: {e}")
            return False
    
    async def _get_admin_users(self, customer_id: str):
        """Get admin users for notification"""
        try:
            users = await user_service.get_users_by_customer(customer_id)
            return [user for user in users if user.role in ['admin', 'system_admin'] and user.is_active]
        except Exception:
            return []
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            # Skip actual email sending in development/testing
            if self.smtp_server == "localhost" and not self.smtp_username:
                print(f"Mock email sent to {to_email}: {subject}")
                return True
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create HTML and text versions
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(self._convert_to_html(body), 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.smtp_username and self.smtp_password:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _create_alert_email_body(self, alert: Dict[str, Any]) -> str:
        """Create email body for security alerts"""
        severity_emoji = {
            'high': '🚨',
            'medium': '⚠️',
            'low': 'ℹ️'
        }
        
        emoji = severity_emoji.get(alert.get('severity', 'medium'), '⚠️')
        
        body = f"""
{emoji} DMARC Security Alert

Alert: {alert['title']}
Severity: {alert.get('severity', 'medium').upper()}
Time: {alert.get('created_at', 'Unknown')}

Description:
{alert['description']}

Details:
"""
        
        # Add specific alert data
        if 'data' in alert:
            for key, value in alert['data'].items():
                body += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        body += f"""

Please review your DMARC Analytics dashboard for more details.

This is an automated alert from your DMARC Analytics Platform.
"""
        
        return body
    
    def _create_summary_email_body(self, summary: Dict[str, Any]) -> str:
        """Create email body for weekly summary"""
        body = f"""
📊 Weekly DMARC Analytics Summary

Email Authentication Overview:
- Total Emails: {summary.get('total_emails', 0):,}
- Passed Authentication: {summary.get('passed_emails', 0):,}
- Failed Authentication: {summary.get('failed_emails', 0):,}
- Pass Rate: {summary.get('pass_rate', 0):.1f}%

Top Email Services:
"""
        
        for service in summary.get('top_services', [])[:5]:
            body += f"- {service.get('service', 'Unknown')}: {service.get('email_count', 0):,} emails\n"
        
        body += """

Recommendations:
- Review failed authentication sources
- Ensure all legitimate services are properly configured
- Monitor for unusual activity patterns

Access your dashboard for detailed analytics and configuration guidance.

Best regards,
DMARC Analytics Platform
"""
        
        return body
    
    def _create_dns_change_email_body(self, domain: str, changes: List[str]) -> str:
        """Create email body for DNS change notifications"""
        body = f"""
🔧 DNS Record Changes Detected

Domain: {domain}
Detection Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Changes Detected:
"""
        
        for change in changes:
            body += f"- {change}\n"
        
        body += """

Please verify these changes are legitimate and update your email authentication configuration if necessary.

If you did not make these changes, please investigate immediately.

DMARC Analytics Platform
"""
        
        return body
    
    def _convert_to_html(self, text: str) -> str:
        """Convert plain text to basic HTML"""
        html = text.replace('\n', '<br>\n')
        html = f"<html><body><pre style='font-family: Arial, sans-serif; white-space: pre-wrap;'>{html}</pre></body></html>"
        return html
    
    async def _log_notification(self, customer_id: str, alert_id: str, notification_type: str, recipients: List):
        """Log notification for audit purposes"""
        try:
            log_entry = {
                'id': str(uuid.uuid4()),
                'customer_id': customer_id,
                'alert_id': alert_id,
                'notification_type': notification_type,
                'recipients': [user.email for user in recipients],
                'sent_at': datetime.utcnow().isoformat(),
                'status': 'sent'
            }
            
            await es_service.index_document("notifications", log_entry['id'], log_entry)
        except Exception as e:
            print(f"Failed to log notification: {e}")
    
    async def get_notification_preferences(self, customer_id: str) -> Dict[str, Any]:
        """Get notification preferences for customer"""
        # This would typically be stored in a database
        # For now, return default preferences
        return {
            'email_alerts': True,
            'weekly_summary': True,
            'dns_change_alerts': True,
            'high_severity_only': False,
            'alert_threshold': {
                'failure_rate': 50.0,
                'volume_spike': 2.0
            }
        }
    
    async def update_notification_preferences(self, customer_id: str, preferences: Dict[str, Any]) -> bool:
        """Update notification preferences for customer"""
        try:
            # Store preferences in Elasticsearch
            await es_service.index_document("notification_preferences", customer_id, preferences)
            return True
        except Exception:
            return False

notification_service = NotificationService()