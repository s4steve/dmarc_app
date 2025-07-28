import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  BookOpenIcon,
  ClipboardDocumentIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface ServiceConfig {
  name: string;
  description: string;
  spf_include: string;
  dkim_setup: string[];
  spf_setup: string[];
  verification_steps: string[];
}

interface Guidance {
  basics?: string[];
  common_mechanisms?: string[];
  best_practices?: string[];
  overview?: string[];
  setup_steps?: string[];
  dns_record_format?: string[];
  troubleshooting?: string[];
  policy_levels?: Record<string, any>;
  implementation_steps?: string[];
  required_tags?: string[];
  optional_tags?: string[];
}

const ConfigurationGuide: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('services');
  const [selectedService, setSelectedService] = useState<string>('');
  const [serviceConfigs, setServiceConfigs] = useState<Record<string, ServiceConfig>>({});
  const [spfGuidance, setSpfGuidance] = useState<Guidance>({});
  const [dmarcGuidance, setDmarcGuidance] = useState<Guidance>({});
  const [dkimGuidance, setDkimGuidance] = useState<Guidance>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadConfigurationData();
  }, []);

  const loadConfigurationData = async () => {
    try {
      setIsLoading(true);
      
      // Mock configuration data
      const mockServiceConfigs: Record<string, ServiceConfig> = {
        "Mailchimp": {
          name: "Mailchimp",
          description: "Email marketing platform for newsletters and campaigns",
          spf_include: "include:servers.mcsv.net",
          dkim_setup: [
            "1. Log in to your Mailchimp account",
            "2. Go to Account > Settings > Domains",
            "3. Click 'Add Domain' and enter your domain",
            "4. Copy the DKIM record provided by Mailchimp",
            "5. Add the DKIM record to your DNS with selector 'k1'"
          ],
          spf_setup: [
            "1. Add 'include:servers.mcsv.net' to your SPF record",
            "2. Ensure your SPF record ends with '-all' or '~all'",
            "3. Example: 'v=spf1 include:servers.mcsv.net -all'"
          ],
          verification_steps: [
            "1. Send a test email through Mailchimp",
            "2. Check DMARC reports for authentication results",
            "3. Verify SPF and DKIM both pass"
          ]
        },
        "SendGrid": {
          name: "SendGrid",
          description: "Cloud-based email delivery platform",
          spf_include: "include:sendgrid.net",
          dkim_setup: [
            "1. Log in to SendGrid dashboard",
            "2. Go to Settings > Sender Authentication",
            "3. Select 'Authenticate Your Domain'",
            "4. Enter your domain and follow the wizard",
            "5. Add the provided DNS records to your domain"
          ],
          spf_setup: [
            "1. Add 'include:sendgrid.net' to your SPF record",
            "2. Example: 'v=spf1 include:sendgrid.net -all'"
          ],
          verification_steps: [
            "1. Use SendGrid's domain verification tool",
            "2. Send test emails and monitor DMARC reports",
            "3. Confirm both SPF and DKIM authentication pass"
          ]
        },
        "Google Workspace": {
          name: "Google Workspace",
          description: "Google's business email and productivity suite",
          spf_include: "include:_spf.google.com",
          dkim_setup: [
            "1. Sign in to Google Admin console",
            "2. Go to Apps > Google Workspace > Gmail",
            "3. Click 'Authenticate email'",
            "4. Generate DKIM key for your domain",
            "5. Add the TXT record to your DNS"
          ],
          spf_setup: [
            "1. Add 'include:_spf.google.com' to your SPF record",
            "2. Example: 'v=spf1 include:_spf.google.com -all'"
          ],
          verification_steps: [
            "1. Check DKIM status in Google Admin console",
            "2. Send test email from Gmail",
            "3. Verify authentication in email headers"
          ]
        }
      };

      const mockSpfGuidance: Guidance = {
        basics: [
          "SPF (Sender Policy Framework) authorizes IP addresses to send email for your domain",
          "Always start with 'v=spf1'",
          "End with '-all' for strict policy or '~all' for soft fail",
          "Keep DNS lookups under 10 to avoid errors"
        ],
        common_mechanisms: [
          "ip4:192.168.1.1 - Authorize specific IPv4 address",
          "ip6:2001:db8::1 - Authorize specific IPv6 address",
          "include:_spf.google.com - Include another domain's SPF record",
          "mx - Authorize your domain's MX record servers",
          "a - Authorize your domain's A record servers"
        ],
        best_practices: [
          "Use 'include:' for third-party services",
          "Regularly audit and remove unused includes",
          "Monitor DMARC reports to identify legitimate senders",
          "Test changes before implementing strict policies"
        ]
      };

      const mockDmarcGuidance: Guidance = {
        policy_levels: {
          none: {
            description: "Monitor only - no action taken on failures",
            recommended_for: "Initial deployment and monitoring",
            example: "v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com"
          },
          quarantine: {
            description: "Failed emails go to spam/junk folder",
            recommended_for: "After monitoring phase shows good alignment",
            example: "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"
          },
          reject: {
            description: "Failed emails are rejected completely",
            recommended_for: "Full protection after successful quarantine phase",
            example: "v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com"
          }
        },
        implementation_steps: [
          "1. Deploy SPF and DKIM for all legitimate email sources",
          "2. Start with p=none policy and collect reports",
          "3. Analyze reports and fix any authentication issues",
          "4. Gradually move to p=quarantine then p=reject",
          "5. Monitor reports continuously for new issues"
        ],
        required_tags: [
          "v=DMARC1 - Version identifier (required)",
          "p= - Policy for domain (none/quarantine/reject)",
          "rua= - Aggregate report email address"
        ],
        optional_tags: [
          "sp= - Policy for subdomains",
          "pct= - Percentage of emails to apply policy to",
          "ruf= - Forensic report email address",
          "ri= - Report interval in seconds"
        ]
      };

      const mockDkimGuidance: Guidance = {
        overview: [
          "DKIM (DomainKeys Identified Mail) adds cryptographic signature to emails",
          "Verifies email hasn't been tampered with in transit",
          "Requires public/private key pair"
        ],
        setup_steps: [
          "1. Generate DKIM key pair (usually done by email service)",
          "2. Add public key as TXT record in DNS",
          "3. Configure email service to sign messages with private key",
          "4. Test DKIM signature using email authentication tools"
        ],
        dns_record_format: [
          "Record name: selector._domainkey.yourdomain.com",
          "Record type: TXT",
          "Value: v=DKIM1; k=rsa; p=<public_key>",
          "TTL: 3600 (1 hour) or as recommended by service"
        ],
        troubleshooting: [
          "Verify DNS record is properly published",
          "Check selector name matches service configuration",
          "Ensure public key is correctly formatted",
          "Test with DKIM validation tools"
        ]
      };

      setServiceConfigs(mockServiceConfigs);
      setSpfGuidance(mockSpfGuidance);
      setDmarcGuidance(mockDmarcGuidance);
      setDkimGuidance(mockDkimGuidance);
      
      if (Object.keys(mockServiceConfigs).length > 0) {
        setSelectedService(Object.keys(mockServiceConfigs)[0]);
      }
    } catch (error) {
      console.error('Failed to load configuration data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const renderServiceConfiguration = () => {
    if (!selectedService || !serviceConfigs[selectedService]) {
      return <div>Select a service to view configuration instructions.</div>;
    }

    const config = serviceConfigs[selectedService];

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div style={{ 
          backgroundColor: '#EFF6FF', 
          border: '1px solid #BFDBFE', 
          borderRadius: '0.5rem', 
          padding: '1rem' 
        }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '500', 
            color: '#1E3A8A', 
            display: 'flex', 
            alignItems: 'center' 
          }}>
            <InformationCircleIcon style={{ height: '1.25rem', width: '1.25rem', marginRight: '0.5rem' }} />
            {config.name}
          </h3>
          <p style={{ color: '#1D4ED8', marginTop: '0.25rem' }}>{config.description}</p>
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
          gap: '1.5rem' 
        }}>
          {/* SPF Setup */}
          <div style={{ 
            backgroundColor: 'white', 
            border: '1px solid #E5E7EB', 
            borderRadius: '0.5rem', 
            padding: '1rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
          }}>
            <h4 style={{ fontSize: '1rem', fontWeight: '500', color: '#111827', marginBottom: '0.75rem' }}>SPF Configuration</h4>
            <div style={{ marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Include directive:</span>
              <div style={{ display: 'flex', alignItems: 'center', marginTop: '0.25rem' }}>
                <code style={{ 
                  backgroundColor: '#F3F4F6', 
                  padding: '0.25rem 0.5rem', 
                  borderRadius: '0.25rem', 
                  fontSize: '0.875rem', 
                  flex: 1,
                  fontFamily: 'monospace'
                }}>
                  {config.spf_include}
                </code>
                <button
                  onClick={() => copyToClipboard(config.spf_include)}
                  style={{
                    marginLeft: '0.5rem',
                    padding: '0.25rem',
                    color: '#9CA3AF',
                    backgroundColor: 'transparent',
                    border: 'none',
                    borderRadius: '0.25rem',
                    cursor: 'pointer',
                    transition: 'color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#4B5563'}
                  onMouseLeave={(e) => e.currentTarget.style.color = '#9CA3AF'}
                >
                  <ClipboardDocumentIcon style={{ height: '1rem', width: '1rem' }} />
                </button>
              </div>
            </div>
            <div>
              <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Setup steps:</span>
              <ol style={{ 
                fontSize: '0.875rem', 
                color: '#4B5563', 
                marginTop: '0.25rem', 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '0.25rem' 
              }}>
                {config.spf_setup.map((step, index) => (
                  <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <span style={{ marginRight: '0.5rem' }}>{index + 1}.</span>
                    <span>{step.replace(/^\d+\.\s*/, '')}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          {/* DKIM Setup */}
          <div style={{ 
            backgroundColor: 'white', 
            border: '1px solid #E5E7EB', 
            borderRadius: '0.5rem', 
            padding: '1rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
          }}>
            <h4 style={{ fontSize: '1rem', fontWeight: '500', color: '#111827', marginBottom: '0.75rem' }}>DKIM Configuration</h4>
            <ol style={{ 
              fontSize: '0.875rem', 
              color: '#4B5563', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '0.5rem' 
            }}>
              {config.dkim_setup.map((step, index) => (
                <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '1.25rem',
                    height: '1.25rem',
                    backgroundColor: '#DBEAFE',
                    color: '#2563EB',
                    fontSize: '0.75rem',
                    fontWeight: '500',
                    borderRadius: '50%',
                    marginRight: '0.5rem',
                    flexShrink: 0,
                    marginTop: '0.125rem'
                  }}>
                    {index + 1}
                  </span>
                  <span>{step.replace(/^\d+\.\s*/, '')}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>

        {/* Verification Steps */}
        <div style={{ 
          backgroundColor: 'white', 
          border: '1px solid #E5E7EB', 
          borderRadius: '0.5rem', 
          padding: '1rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
        }}>
          <h4 style={{ fontSize: '1rem', fontWeight: '500', color: '#111827', marginBottom: '0.75rem' }}>Verification Steps</h4>
          <ol style={{ 
            fontSize: '0.875rem', 
            color: '#4B5563', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '0.5rem' 
          }}>
            {config.verification_steps.map((step, index) => (
              <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                <CheckCircleIcon style={{ height: '1rem', width: '1rem', color: '#10B981', marginRight: '0.5rem', flexShrink: 0, marginTop: '0.125rem' }} />
                <span>{step.replace(/^\d+\.\s*/, '')}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    );
  };

  const renderGuidanceSection = (guidance: Guidance, title: string) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {Object.entries(guidance).map(([key, value]) => (
        <div key={key} style={{ 
          backgroundColor: 'white', 
          border: '1px solid #E5E7EB', 
          borderRadius: '0.5rem', 
          padding: '1rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
        }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '500', 
            color: '#111827', 
            marginBottom: '0.75rem', 
            textTransform: 'capitalize' 
          }}>
            {key.replace(/_/g, ' ')}
          </h3>
          
          {Array.isArray(value) ? (
            <ul style={{ 
              fontSize: '0.875rem', 
              color: '#4B5563', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '0.5rem' 
            }}>
              {value.map((item, index) => (
                <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                  <span style={{
                    display: 'inline-block',
                    width: '0.5rem',
                    height: '0.5rem',
                    backgroundColor: '#3B82F6',
                    borderRadius: '50%',
                    marginRight: '0.75rem',
                    marginTop: '0.5rem',
                    flexShrink: 0
                  }}></span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          ) : typeof value === 'object' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {Object.entries(value).map(([subKey, subValue]) => (
                <div key={subKey} style={{ 
                  borderLeft: '4px solid #60A5FA', 
                  paddingLeft: '1rem' 
                }}>
                  <h4 style={{ 
                    fontWeight: '500', 
                    color: '#111827', 
                    textTransform: 'capitalize' 
                  }}>{subKey}</h4>
                  {typeof subValue === 'object' && subValue !== null ? (
                    <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#4B5563' }}>
                      {Object.entries(subValue).map(([prop, val]) => (
                        <p key={prop} style={{ marginTop: '0.25rem' }}>
                          <span style={{ fontWeight: '500' }}>{prop.replace(/_/g, ' ')}: </span>
                          {String(val)}
                        </p>
                      ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: '0.875rem', color: '#4B5563', marginTop: '0.25rem' }}>{String(subValue)}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: '0.875rem', color: '#4B5563' }}>{String(value)}</p>
          )}
        </div>
      ))}
    </div>
  );

  const tabs = [
    { id: 'services', name: 'Service Setup', icon: BookOpenIcon },
    { id: 'spf', name: 'SPF Guide', icon: InformationCircleIcon },
    { id: 'dmarc', name: 'DMARC Guide', icon: ExclamationTriangleIcon },
    { id: 'dkim', name: 'DKIM Guide', icon: CheckCircleIcon },
  ];

  if (isLoading) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '16rem' }}>
          <div style={{ 
            animation: 'spin 1s linear infinite', 
            borderRadius: '50%', 
            height: '8rem', 
            width: '8rem', 
            borderBottom: '2px solid #2563EB' 
          }}></div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
      <div style={{ padding: '1.5rem 0' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#111827' }}>Configuration Guide</h1>
          <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
            Step-by-step instructions for configuring email authentication
          </p>
        </div>

        {/* Tab Navigation */}
        <div style={{ borderBottom: '1px solid #E5E7EB', marginBottom: '1.5rem' }}>
          <nav style={{ marginBottom: '-1px', display: 'flex', gap: '2rem' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  whiteSpace: 'nowrap',
                  padding: '0.5rem 0.25rem',
                  borderBottom: `2px solid ${activeTab === tab.id ? '#3B82F6' : 'transparent'}`,
                  fontWeight: '500',
                  fontSize: '0.875rem',
                  display: 'flex',
                  alignItems: 'center',
                  color: activeTab === tab.id ? '#2563EB' : '#6B7280',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.color = '#374151';
                    e.currentTarget.style.borderBottomColor = '#D1D5DB';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.color = '#6B7280';
                    e.currentTarget.style.borderBottomColor = 'transparent';
                  }
                }}
              >
                <tab.icon style={{ height: '1rem', width: '1rem', marginRight: '0.5rem' }} />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'services' && (
          <div>
            {Object.keys(serviceConfigs).length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ 
                  display: 'block', 
                  fontSize: '0.875rem', 
                  fontWeight: '500', 
                  color: '#374151', 
                  marginBottom: '0.5rem' 
                }}>
                  Select Email Service:
                </label>
                <select
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  style={{
                    display: 'block',
                    width: '100%',
                    maxWidth: '20rem',
                    border: '1px solid #D1D5DB',
                    borderRadius: '0.375rem',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.875rem',
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                    backgroundColor: 'white'
                  }}
                >
                  {Object.keys(serviceConfigs).map((serviceName) => (
                    <option key={serviceName} value={serviceName}>
                      {serviceName}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {renderServiceConfiguration()}
          </div>
        )}

        {activeTab === 'spf' && renderGuidanceSection(spfGuidance, 'SPF')}
        {activeTab === 'dmarc' && renderGuidanceSection(dmarcGuidance, 'DMARC')}
        {activeTab === 'dkim' && renderGuidanceSection(dkimGuidance, 'DKIM')}
      </div>
    </div>
  );
};

export default ConfigurationGuide;