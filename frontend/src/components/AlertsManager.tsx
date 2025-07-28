import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDomain } from '../contexts/DomainContext';
import { 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon,
  ClockIcon,
  ShieldExclamationIcon
} from '@heroicons/react/24/outline';

interface Alert {
  id: string;
  alert_type: string;
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  created_at: string;
  resolved: boolean;
  data?: Record<string, any>;
}

const AlertsManager: React.FC = () => {
  const { user } = useAuth();
  const { selectedDomain } = useDomain();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [selectedDays, setSelectedDays] = useState(7);

  useEffect(() => {
    loadAlerts();
  }, [selectedDays, selectedDomain]);

  const loadAlerts = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Only load alerts if a domain is selected
      if (!selectedDomain) {
        setAlerts([]);
        setIsLoading(false);
        return;
      }
      
      // Mock data for alerts since API endpoints exist but may not have data
      // In a real implementation, this would filter alerts by selectedDomain.name
      const mockAlerts: Alert[] = [
        {
          id: '1',
          alert_type: 'high_failure_rate',
          severity: 'high',
          title: `High DMARC Failure Rate Detected for ${selectedDomain.name}`,
          description: `DMARC authentication failure rate is 65.2% (threshold: 50%) for domain ${selectedDomain.name}`,
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          resolved: false,
          data: {
            pass_rate: 34.8,
            failed_emails: 1450,
            total_emails: 2224
          }
        },
        {
          id: '2',
          alert_type: 'unknown_senders',
          severity: 'medium',
          title: 'Unknown Email Senders Detected',
          description: '15 emails from unidentified senders in the last 24 hours',
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          resolved: false,
          data: {
            unknown_email_count: 15
          }
        },
        {
          id: '3',
          alert_type: 'volume_spike',
          severity: 'medium',
          title: 'Email Volume Spike Detected',
          description: 'Email volume increased to 5,230 (average: 1,850)',
          created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
          resolved: true,
          data: {
            current_volume: 5230,
            average_volume: 1850,
            spike_ratio: 2.83
          }
        }
      ];
      
      setAlerts(mockAlerts);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load alerts');
    } finally {
      setIsLoading(false);
    }
  };

  const resolveAlert = async (alertId: string) => {
    try {
      // Update alert locally
      setAlerts(prevAlerts => 
        prevAlerts.map(alert => 
          alert.id === alertId ? { ...alert, resolved: true } : alert
        )
      );
    } catch (err: any) {
      setError('Failed to resolve alert');
    }
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'high':
        return { color: '#DC2626', backgroundColor: '#FEF2F2', borderColor: '#FECACA' };
      case 'medium':
        return { color: '#D97706', backgroundColor: '#FFFBEB', borderColor: '#FDE68A' };
      case 'low':
        return { color: '#2563EB', backgroundColor: '#EFF6FF', borderColor: '#DBEAFE' };
      default:
        return { color: '#4B5563', backgroundColor: '#F9FAFB', borderColor: '#E5E7EB' };
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <ShieldExclamationIcon style={{ height: '1.25rem', width: '1.25rem', color: '#EF4444' }} />;
      case 'medium':
        return <ExclamationTriangleIcon style={{ height: '1.25rem', width: '1.25rem', color: '#F59E0B' }} />;
      case 'low':
        return <ExclamationTriangleIcon style={{ height: '1.25rem', width: '1.25rem', color: '#3B82F6' }} />;
      default:
        return <ExclamationTriangleIcon style={{ height: '1.25rem', width: '1.25rem', color: '#6B7280' }} />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const activeAlerts = alerts.filter(alert => !alert.resolved);
  const resolvedAlerts = alerts.filter(alert => alert.resolved);

  if (!selectedDomain) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '16rem' }}>
          <div style={{ fontSize: '1.125rem', fontWeight: '500', color: '#6B7280', marginBottom: '0.5rem' }}>
            No Domain Selected
          </div>
          <div style={{ fontSize: '0.875rem', color: '#9CA3AF', textAlign: 'center' }}>
            Please select a domain from the header to view security alerts for that domain.
          </div>
        </div>
      </div>
    );
  }

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

  if (error) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ 
          backgroundColor: '#FEF2F2', 
          border: '1px solid #FECACA', 
          color: '#DC2626', 
          padding: '1rem', 
          borderRadius: '0.375rem' 
        }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
      <div style={{ padding: '1.5rem 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#111827' }}>Security Alerts</h1>
            <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
              Monitor and manage security alerts for {selectedDomain?.name}
              <span style={{ marginLeft: '0.5rem', padding: '0.125rem 0.5rem', backgroundColor: '#EFF6FF', color: '#2563EB', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: '500' }}>
                {selectedDomain?.name}
              </span>
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setSelectedDays(days)}
                style={{
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  borderRadius: '0.375rem',
                  border: '1px solid #D1D5DB',
                  backgroundColor: selectedDays === days ? '#2563EB' : 'white',
                  color: selectedDays === days ? 'white' : '#374151',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  if (selectedDays !== days) {
                    e.currentTarget.style.backgroundColor = '#F9FAFB';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedDays !== days) {
                    e.currentTarget.style.backgroundColor = 'white';
                  }
                }}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>

        {/* Active Alerts */}
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: '500', color: '#111827', marginBottom: '1rem' }}>
            Active Alerts ({activeAlerts.length})
          </h2>
          
          {activeAlerts.length === 0 ? (
            <div style={{ backgroundColor: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '0.5rem', padding: '1.5rem', textAlign: 'center' }}>
              <CheckCircleIcon style={{ margin: '0 auto', height: '3rem', width: '3rem', color: '#10B981', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.125rem', fontWeight: '500', color: '#14532D', marginBottom: '0.5rem' }}>All Clear!</h3>
              <p style={{ color: '#15803D' }}>No active security alerts at this time.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {activeAlerts.map((alert) => {
                const severityStyle = getSeverityStyle(alert.severity);
                return (
                  <div
                    key={alert.id}
                    style={{
                      border: `1px solid ${severityStyle.borderColor}`,
                      borderRadius: '0.5rem',
                      padding: '1rem',
                      backgroundColor: severityStyle.backgroundColor,
                      color: severityStyle.color
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                        {getSeverityIcon(alert.severity)}
                        <div style={{ flex: 1 }}>
                          <h3 style={{ fontSize: '0.875rem', fontWeight: '500' }}>{alert.title}</h3>
                          <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>{alert.description}</p>
                        
                          {alert.data && (
                            <div style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
                              {Object.entries(alert.data).map(([key, value]) => (
                                <span key={key} style={{ display: 'inline-block', marginRight: '1rem' }}>
                                  <strong>{key.replace('_', ' ')}:</strong> {String(value)}
                                </span>
                              ))}
                            </div>
                          )}
                        
                        <div style={{ display: 'flex', alignItems: 'center', marginTop: '0.5rem', fontSize: '0.75rem' }}>
                          <ClockIcon style={{ height: '0.75rem', width: '0.75rem', marginRight: '0.25rem' }} />
                          {formatTimestamp(alert.created_at)}
                        </div>
                      </div>
                    </div>
                      
                      <button
                        onClick={() => resolveAlert(alert.id)}
                        style={{
                          marginLeft: '1rem',
                          padding: '0.25rem',
                          borderRadius: '0.25rem',
                          backgroundColor: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        <XMarkIcon style={{ height: '1rem', width: '1rem' }} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Resolved Alerts */}
        {resolvedAlerts.length > 0 && (
          <div>
            <h2 style={{ fontSize: '1.125rem', fontWeight: '500', color: '#111827', marginBottom: '1rem' }}>
              Resolved Alerts ({resolvedAlerts.length})
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {resolvedAlerts.map((alert) => (
                <div
                  key={alert.id}
                  style={{
                    border: '1px solid #E5E7EB',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '0.5rem',
                    padding: '1rem',
                    opacity: 0.75
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                    <CheckCircleIcon style={{ height: '1.25rem', width: '1.25rem', color: '#10B981' }} />
                    <div style={{ flex: 1 }}>
                      <h3 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>{alert.title}</h3>
                      <p style={{ fontSize: '0.875rem', color: '#4B5563', marginTop: '0.25rem' }}>{alert.description}</p>
                      
                      <div style={{ display: 'flex', alignItems: 'center', marginTop: '0.5rem', fontSize: '0.75rem', color: '#6B7280' }}>
                        <ClockIcon style={{ height: '0.75rem', width: '0.75rem', marginRight: '0.25rem' }} />
                        {formatTimestamp(alert.created_at)} • Resolved
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsManager;