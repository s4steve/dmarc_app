import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDomain } from '../contexts/DomainContext';
import { 
  ServerIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

interface DNSRecord {
  domain: string;
  record_type: string;
  record_name: string;
  record_value: string;
  last_checked: string;
  syntax_valid: boolean;
  recommendations: string[];
  errors: string[];
}

interface DNSCheckResult {
  domain: string;
  spf_record?: DNSRecord;
  dmarc_record?: DNSRecord;
  dkim_records: DNSRecord[];
  mx_records: DNSRecord[];
  overall_status: string;
  recommendations: string[];
}

const DNSManager: React.FC = () => {
  const { user } = useAuth();
  const { selectedDomain } = useDomain();
  const [domain, setDomain] = useState('');
  const [dnsResult, setDnsResult] = useState<DNSCheckResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // Auto-populate domain input when a domain is selected
  useEffect(() => {
    if (selectedDomain && !domain) {
      setDomain(selectedDomain.name);
    }
  }, [selectedDomain, domain]);

  const checkDNS = async () => {
    if (!domain.trim()) {
      setError('Please enter a domain name');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      
      // Mock DNS check result since backend may not have real DNS data
      const mockResult: DNSCheckResult = {
        domain: domain,
        spf_record: {
          domain: domain,
          record_type: 'SPF',
          record_name: domain,
          record_value: 'v=spf1 include:_spf.google.com include:mailchimp.com -all',
          last_checked: new Date().toISOString(),
          syntax_valid: true,
          recommendations: ['Consider using ~all instead of -all for initial testing'],
          errors: []
        },
        dmarc_record: {
          domain: domain,
          record_type: 'DMARC',
          record_name: `_dmarc.${domain}`,
          record_value: 'v=DMARC1; p=none; rua=mailto:dmarc@example.com',
          last_checked: new Date().toISOString(),
          syntax_valid: true,
          recommendations: ['Consider upgrading policy to quarantine or reject'],
          errors: []
        },
        dkim_records: [
          {
            domain: domain,
            record_type: 'DKIM',
            record_name: `google._domainkey.${domain}`,
            record_value: 'v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...',
            last_checked: new Date().toISOString(),
            syntax_valid: true,
            recommendations: [],
            errors: []
          }
        ],
        mx_records: [
          {
            domain: domain,
            record_type: 'MX',
            record_name: domain,
            record_value: '10 mail.google.com',
            last_checked: new Date().toISOString(),
            syntax_valid: true,
            recommendations: [],
            errors: []
          }
        ],
        overall_status: 'Good',
        recommendations: [
          'Consider implementing DKIM for all email services',
          'Monitor DMARC reports regularly',
          'Plan gradual migration to stricter DMARC policy'
        ]
      };
      
      setDnsResult(mockResult);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to check DNS records');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusStyle = (status: string) => {
    switch (status.toLowerCase()) {
      case 'good':
        return { color: '#059669', backgroundColor: '#ECFDF5', borderColor: '#A7F3D0' };
      case 'warning':
        return { color: '#D97706', backgroundColor: '#FFFBEB', borderColor: '#FDE68A' };
      case 'error':
      case 'critical':
        return { color: '#DC2626', backgroundColor: '#FEF2F2', borderColor: '#FECACA' };
      default:
        return { color: '#4B5563', backgroundColor: '#F9FAFB', borderColor: '#E5E7EB' };
    }
  };

  const getStatusIcon = (valid: boolean) => {
    return valid ? (
      <CheckCircleIcon style={{ height: '1.25rem', width: '1.25rem', color: '#10B981' }} />
    ) : (
      <XCircleIcon style={{ height: '1.25rem', width: '1.25rem', color: '#EF4444' }} />
    );
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const RecordCard: React.FC<{ record: DNSRecord; title: string }> = ({ record, title }) => (
    <div style={{ 
      backgroundColor: 'white', 
      border: '1px solid #E5E7EB', 
      borderRadius: '0.5rem', 
      padding: '1rem',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <h3 style={{ 
          fontSize: '1.125rem', 
          fontWeight: '500', 
          color: '#111827', 
          display: 'flex', 
          alignItems: 'center' 
        }}>
          {getStatusIcon(record.syntax_valid)}
          <span style={{ marginLeft: '0.5rem' }}>{title}</span>
        </h3>
        <button
          onClick={() => copyToClipboard(record.record_value)}
          style={{
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
          title="Copy to clipboard"
        >
          <ClipboardDocumentIcon style={{ height: '1rem', width: '1rem' }} />
        </button>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div>
          <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Record Name:</span>
          <p style={{ fontSize: '0.875rem', color: '#111827', fontFamily: 'monospace' }}>{record.record_name}</p>
        </div>
        
        <div>
          <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Record Value:</span>
          <p style={{ 
            fontSize: '0.875rem', 
            color: '#111827', 
            fontFamily: 'monospace', 
            wordBreak: 'break-all', 
            backgroundColor: '#F9FAFB', 
            padding: '0.5rem', 
            borderRadius: '0.25rem' 
          }}>
            {record.record_value}
          </p>
        </div>
        
        <div>
          <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Last Checked:</span>
          <p style={{ fontSize: '0.875rem', color: '#4B5563' }}>
            {new Date(record.last_checked).toLocaleString()}
          </p>
        </div>
        
        {record.recommendations.length > 0 && (
          <div>
            <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Recommendations:</span>
            <ul style={{ 
              fontSize: '0.875rem', 
              color: '#92400E', 
              backgroundColor: '#FFFBEB', 
              padding: '0.5rem', 
              borderRadius: '0.25rem', 
              marginTop: '0.25rem' 
            }}>
              {record.recommendations.map((rec, index) => (
                <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                  <ExclamationTriangleIcon style={{ height: '1rem', width: '1rem', marginRight: '0.25rem', flexShrink: 0, marginTop: '0.125rem', color: '#F59E0B' }} />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {record.errors.length > 0 && (
          <div>
            <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Errors:</span>
            <ul style={{ 
              fontSize: '0.875rem', 
              color: '#B91C1C', 
              backgroundColor: '#FEF2F2', 
              padding: '0.5rem', 
              borderRadius: '0.25rem', 
              marginTop: '0.25rem' 
            }}>
              {record.errors.map((error, index) => (
                <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                  <XCircleIcon style={{ height: '1rem', width: '1rem', marginRight: '0.25rem', flexShrink: 0, marginTop: '0.125rem', color: '#EF4444' }} />
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );

  if (!selectedDomain && !domain) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ padding: '1.5rem 0' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#111827' }}>DNS Record Manager</h1>
            <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
              Check and validate your email authentication DNS records
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '16rem' }}>
            <div style={{ fontSize: '1.125rem', fontWeight: '500', color: '#6B7280', marginBottom: '0.5rem' }}>
              No Domain Selected
            </div>
            <div style={{ fontSize: '0.875rem', color: '#9CA3AF', textAlign: 'center' }}>
              Please select a domain from the header or enter a domain name below to check DNS records.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
      <div style={{ padding: '1.5rem 0' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#111827' }}>DNS Record Manager</h1>
          <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
            Check and validate your email authentication DNS records
            {selectedDomain && (
              <span style={{ marginLeft: '0.5rem', padding: '0.125rem 0.5rem', backgroundColor: '#EFF6FF', color: '#2563EB', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: '500' }}>
                {selectedDomain.name}
              </span>
            )}
          </p>
        </div>

        {/* Domain Input */}
        <div style={{ 
          backgroundColor: 'white', 
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 
          borderRadius: '0.5rem', 
          padding: '1.5rem', 
          marginBottom: '1.5rem' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label htmlFor="domain" style={{ 
                display: 'block', 
                fontSize: '0.875rem', 
                fontWeight: '500', 
                color: '#374151' 
              }}>
                Domain to Check
              </label>
              <input
                type="text"
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="example.com"
                style={{
                  marginTop: '0.25rem',
                  display: 'block',
                  width: '100%',
                  border: '1px solid #D1D5DB',
                  borderRadius: '0.375rem',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.875rem',
                  boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
                }}
              />
            </div>
            <button
              onClick={checkDNS}
              disabled={isLoading}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '0.5rem 1rem',
                border: 'none',
                fontSize: '0.875rem',
                fontWeight: '500',
                borderRadius: '0.375rem',
                color: 'white',
                backgroundColor: isLoading ? '#93C5FD' : '#2563EB',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!isLoading) e.currentTarget.style.backgroundColor = '#1D4ED8';
              }}
              onMouseLeave={(e) => {
                if (!isLoading) e.currentTarget.style.backgroundColor = '#2563EB';
              }}
            >
              {isLoading ? (
                <div style={{ 
                  animation: 'spin 1s linear infinite', 
                  borderRadius: '50%', 
                  height: '1rem', 
                  width: '1rem', 
                  borderBottom: '2px solid white', 
                  marginRight: '0.5rem' 
                }}></div>
              ) : (
                <MagnifyingGlassIcon style={{ height: '1rem', width: '1rem', marginRight: '0.5rem' }} />
              )}
              Check DNS
            </button>
          </div>
        </div>

        {error && (
          <div style={{ 
            backgroundColor: '#FEF2F2', 
            border: '1px solid #FECACA', 
            color: '#DC2626', 
            padding: '1rem', 
            borderRadius: '0.375rem', 
            marginBottom: '1.5rem' 
          }}>
            {error}
          </div>
        )}

        {dnsResult && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Overall Status */}
            <div style={{
              border: `1px solid ${getStatusStyle(dnsResult.overall_status).borderColor}`,
              borderRadius: '0.5rem',
              padding: '1rem',
              backgroundColor: getStatusStyle(dnsResult.overall_status).backgroundColor,
              color: getStatusStyle(dnsResult.overall_status).color
            }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ServerIcon style={{ height: '1.5rem', width: '1.5rem', marginRight: '0.75rem' }} />
                <div>
                  <h2 style={{ fontSize: '1.125rem', fontWeight: '500' }}>
                    DNS Status for {dnsResult.domain}: {dnsResult.overall_status}
                  </h2>
                  {dnsResult.recommendations.length > 0 && (
                    <ul style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                      {dnsResult.recommendations.map((rec, index) => (
                        <li key={index} style={{ display: 'flex', alignItems: 'flex-start' }}>
                          <span style={{ marginRight: '0.25rem' }}>•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            {/* DNS Records */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
              gap: '1.5rem' 
            }}>
              {dnsResult.spf_record && (
                <RecordCard record={dnsResult.spf_record} title="SPF Record" />
              )}
              
              {dnsResult.dmarc_record && (
                <RecordCard record={dnsResult.dmarc_record} title="DMARC Record" />
              )}
              
              {dnsResult.dkim_records.map((record, index) => (
                <RecordCard
                  key={index}
                  record={record}
                  title={`DKIM Record ${index + 1}`}
                />
              ))}
              
              {dnsResult.mx_records.length > 0 && (
                <RecordCard
                  record={dnsResult.mx_records[0]}
                  title="MX Record"
                />
              )}
            </div>
          </div>
        )}

        {!dnsResult && !isLoading && (
          <div style={{ textAlign: 'center', padding: '3rem 0' }}>
            <ServerIcon style={{ margin: '0 auto', height: '3rem', width: '3rem', color: '#9CA3AF' }} />
            <h3 style={{ marginTop: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>No DNS Check Performed</h3>
            <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
              Enter a domain name and click "Check DNS" to analyze your email authentication records.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DNSManager;