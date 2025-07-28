from typing import Dict, List, Optional
from ..models.dmarc import ThirdPartyService
from .elasticsearch import es_service

class ConfigurationService:
    def __init__(self):
        self.service_configurations = self._get_service_configurations()
    
    def _get_service_configurations(self) -> Dict[str, Dict]:
        return {
            "Mailchimp": {
                "name": "Mailchimp",
                "description": "Email marketing platform for newsletters and campaigns",
                "spf_include": "include:servers.mcsv.net",
                "dkim_setup": [
                    "1. Log in to your Mailchimp account",
                    "2. Go to Account > Settings > Domains",
                    "3. Click 'Add Domain' and enter your domain",
                    "4. Copy the DKIM record provided by Mailchimp",
                    "5. Add the DKIM record to your DNS with selector 'k1'"
                ],
                "spf_setup": [
                    "1. Add 'include:servers.mcsv.net' to your SPF record",
                    "2. Ensure your SPF record ends with '-all' or '~all'",
                    "3. Example: 'v=spf1 include:servers.mcsv.net -all'"
                ],
                "verification_steps": [
                    "1. Send a test email through Mailchimp",
                    "2. Check DMARC reports for authentication results",
                    "3. Verify SPF and DKIM both pass"
                ]
            },
            "SendGrid": {
                "name": "SendGrid",
                "description": "Cloud-based email delivery platform",
                "spf_include": "include:sendgrid.net",
                "dkim_setup": [
                    "1. Log in to SendGrid dashboard",
                    "2. Go to Settings > Sender Authentication",
                    "3. Select 'Authenticate Your Domain'",
                    "4. Enter your domain and follow the wizard",
                    "5. Add the provided DNS records to your domain"
                ],
                "spf_setup": [
                    "1. Add 'include:sendgrid.net' to your SPF record",
                    "2. Example: 'v=spf1 include:sendgrid.net -all'"
                ],
                "verification_steps": [
                    "1. Use SendGrid's domain verification tool",
                    "2. Send test emails and monitor DMARC reports",
                    "3. Confirm both SPF and DKIM authentication pass"
                ]
            },
            "Amazon SES": {
                "name": "Amazon SES",
                "description": "Amazon Simple Email Service for transactional emails",
                "spf_include": "include:amazonses.com",
                "dkim_setup": [
                    "1. Open Amazon SES console",
                    "2. Go to Configuration > Verified identities",
                    "3. Select your domain and click 'DKIM'",
                    "4. Enable DKIM signing",
                    "5. Add the three CNAME records to your DNS"
                ],
                "spf_setup": [
                    "1. Add 'include:amazonses.com' to your SPF record",
                    "2. Example: 'v=spf1 include:amazonses.com -all'"
                ],
                "verification_steps": [
                    "1. Check domain verification status in SES console",
                    "2. Send test email and verify DKIM signature",
                    "3. Monitor DMARC reports for authentication results"
                ]
            },
            "Microsoft 365": {
                "name": "Microsoft 365",
                "description": "Microsoft's cloud productivity suite with Exchange Online",
                "spf_include": "include:spf.protection.outlook.com",
                "dkim_setup": [
                    "1. Sign in to Microsoft 365 admin center",
                    "2. Go to Exchange admin center",
                    "3. Navigate to Protection > DKIM",
                    "4. Select your domain and enable DKIM",
                    "5. Add the provided CNAME records to DNS"
                ],
                "spf_setup": [
                    "1. Add 'include:spf.protection.outlook.com' to SPF record",
                    "2. Example: 'v=spf1 include:spf.protection.outlook.com -all'"
                ],
                "verification_steps": [
                    "1. Verify DKIM is enabled in Exchange admin center",
                    "2. Send test email from Outlook",
                    "3. Check message headers for DKIM signature"
                ]
            },
            "Google Workspace": {
                "name": "Google Workspace",
                "description": "Google's business email and productivity suite",
                "spf_include": "include:_spf.google.com",
                "dkim_setup": [
                    "1. Sign in to Google Admin console",
                    "2. Go to Apps > Google Workspace > Gmail",
                    "3. Click 'Authenticate email'",
                    "4. Generate DKIM key for your domain",
                    "5. Add the TXT record to your DNS"
                ],
                "spf_setup": [
                    "1. Add 'include:_spf.google.com' to your SPF record",
                    "2. Example: 'v=spf1 include:_spf.google.com -all'"
                ],
                "verification_steps": [
                    "1. Check DKIM status in Google Admin console",
                    "2. Send test email from Gmail",
                    "3. Verify authentication in email headers"
                ]
            },
            "Constant Contact": {
                "name": "Constant Contact",
                "description": "Email marketing and automation platform",
                "spf_include": "include:spf.constantcontact.com",
                "dkim_setup": [
                    "1. Contact Constant Contact support",
                    "2. Request DKIM setup for your domain",
                    "3. Provide your domain information",
                    "4. Add the DKIM record they provide to DNS"
                ],
                "spf_setup": [
                    "1. Add 'include:spf.constantcontact.com' to SPF record",
                    "2. Example: 'v=spf1 include:spf.constantcontact.com -all'"
                ],
                "verification_steps": [
                    "1. Send test campaign through Constant Contact",
                    "2. Check DMARC reports for authentication status",
                    "3. Verify both SPF and DKIM pass"
                ]
            }
        }
    
    async def get_service_configuration(self, service_name: str) -> Optional[Dict]:
        """Get configuration instructions for a specific service"""
        return self.service_configurations.get(service_name)
    
    async def get_all_service_configurations(self) -> Dict[str, Dict]:
        """Get configuration instructions for all known services"""
        return self.service_configurations
    
    def get_generic_spf_guidance(self) -> Dict[str, List[str]]:
        """Get generic SPF record guidance"""
        return {
            "basics": [
                "SPF (Sender Policy Framework) authorizes IP addresses to send email for your domain",
                "Always start with 'v=spf1'",
                "End with '-all' for strict policy or '~all' for soft fail",
                "Keep DNS lookups under 10 to avoid errors"
            ],
            "common_mechanisms": [
                "ip4:192.168.1.1 - Authorize specific IPv4 address",
                "ip6:2001:db8::1 - Authorize specific IPv6 address",
                "include:_spf.google.com - Include another domain's SPF record",
                "mx - Authorize your domain's MX record servers",
                "a - Authorize your domain's A record servers"
            ],
            "best_practices": [
                "Use 'include:' for third-party services",
                "Regularly audit and remove unused includes",
                "Monitor DMARC reports to identify legitimate senders",
                "Test changes before implementing strict policies"
            ]
        }
    
    def get_dmarc_policy_guidance(self) -> Dict[str, any]:
        """Get DMARC policy configuration guidance"""
        return {
            "policy_levels": {
                "none": {
                    "description": "Monitor only - no action taken on failures",
                    "recommended_for": "Initial deployment and monitoring",
                    "example": "v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com"
                },
                "quarantine": {
                    "description": "Failed emails go to spam/junk folder",
                    "recommended_for": "After monitoring phase shows good alignment",
                    "example": "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"
                },
                "reject": {
                    "description": "Failed emails are rejected completely",
                    "recommended_for": "Full protection after successful quarantine phase",
                    "example": "v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com"
                }
            },
            "implementation_steps": [
                "1. Deploy SPF and DKIM for all legitimate email sources",
                "2. Start with p=none policy and collect reports",
                "3. Analyze reports and fix any authentication issues",
                "4. Gradually move to p=quarantine then p=reject",
                "5. Monitor reports continuously for new issues"
            ],
            "required_tags": [
                "v=DMARC1 - Version identifier (required)",
                "p= - Policy for domain (none/quarantine/reject)",
                "rua= - Aggregate report email address"
            ],
            "optional_tags": [
                "sp= - Policy for subdomains",
                "pct= - Percentage of emails to apply policy to",
                "ruf= - Forensic report email address",
                "ri= - Report interval in seconds"
            ]
        }
    
    def get_dkim_guidance(self) -> Dict[str, List[str]]:
        """Get DKIM configuration guidance"""
        return {
            "overview": [
                "DKIM (DomainKeys Identified Mail) adds cryptographic signature to emails",
                "Verifies email hasn't been tampered with in transit",
                "Requires public/private key pair"
            ],
            "setup_steps": [
                "1. Generate DKIM key pair (usually done by email service)",
                "2. Add public key as TXT record in DNS",
                "3. Configure email service to sign messages with private key",
                "4. Test DKIM signature using email authentication tools"
            ],
            "dns_record_format": [
                "Record name: selector._domainkey.yourdomain.com",
                "Record type: TXT",
                "Value: v=DKIM1; k=rsa; p=<public_key>",
                "TTL: 3600 (1 hour) or as recommended by service"
            ],
            "troubleshooting": [
                "Verify DNS record is properly published",
                "Check selector name matches service configuration",
                "Ensure public key is correctly formatted",
                "Test with DKIM validation tools"
            ]
        }

configuration_service = ConfigurationService()