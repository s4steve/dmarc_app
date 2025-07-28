import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface Service {
  service: string;
  email_count: number;
}

interface ServiceBreakdownProps {
  services: Service[];
}

const ServiceBreakdown: React.FC<ServiceBreakdownProps> = ({ services }) => {
  const totalEmails = services.reduce((sum, service) => sum + service.email_count, 0);
  
  const getServiceColor = (serviceName: string) => {
    const colors = {
      'Google Workspace': '#4285F4',
      'Microsoft 365': '#FF6B35', 
      'Mailchimp': '#FFE01B',
      'SendGrid': '#1A82E2',
      'Amazon SES': '#FF9900',
      'Hubspot': '#FF7A59',
      'Klaviyo': '#7C3AED',
      'Campaign Monitor': '#57BF47',
      'Postmark': '#FFCD02',
      'Salesforce Marketing Cloud': '#00A1E0',
      'Constant Contact': '#1F4B99',
      'Mandrill/Mailchimp Transactional': '#2ECC71',
      'unknown': '#6B7280'
    };
    return colors[serviceName as keyof typeof colors] || '#6B7280';
  };

  const getServiceIcon = (serviceName: string) => {
    if (serviceName === 'unknown') {
      return (
        <div style={{ width: '1rem', height: '1rem', backgroundColor: '#9ca3af', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: '0.75rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'white', fontWeight: 'bold' }}>?</span>
        </div>
      );
    }
    return (
      <div 
        style={{ 
          width: '1rem', 
          height: '1rem', 
          borderRadius: '50%', 
          marginRight: '0.75rem',
          backgroundColor: getServiceColor(serviceName) 
        }}
      />
    );
  };

  const formatServiceName = (serviceName: string) => {
    if (serviceName === 'unknown') {
      return 'Unknown Sources';
    }
    return serviceName;
  };

  const chartData = services.map(service => ({
    name: service.service.length > 15 ? service.service.substring(0, 15) + '...' : service.service,
    fullName: service.service,
    emails: service.email_count,
    fill: getServiceColor(service.service)
  }));

  return (
    <div style={{ backgroundColor: 'white', overflow: 'hidden', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderRadius: '0.5rem' }}>
      <div style={{ padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1.125rem', lineHeight: '1.75rem', fontWeight: '500', color: '#111827', marginBottom: '1rem' }}>
          Email Services Breakdown
        </h3>
        
        {services.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <div style={{ width: '4rem', height: '4rem', margin: '0 auto 1rem', backgroundColor: '#f3f4f6', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg style={{ width: '2rem', height: '2rem', color: '#9ca3af' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>No service data available</p>
            <p style={{ color: '#9ca3af', fontSize: '0.75rem', marginTop: '0.25rem' }}>Upload DMARC reports to see email service breakdown</p>
          </div>
        ) : (
          <>
            <div style={{ height: '16rem', marginBottom: '1.5rem' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" style={{ opacity: 0.3 }} />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 11 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                    interval={0}
                  />
                  <YAxis 
                    tick={{ fontSize: 11 }}
                    tickFormatter={(value) => value.toLocaleString()}
                  />
                  <Tooltip 
                    formatter={(value: any, name: any, props: any) => [
                      `${Number(value).toLocaleString()} emails`,
                      formatServiceName(props.payload.fullName)
                    ]}
                    labelFormatter={(label, payload) => {
                      if (payload && payload[0]) {
                        return formatServiceName(payload[0].payload.fullName);
                      }
                      return label;
                    }}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      fontSize: '14px'
                    }}
                  />
                  <Bar 
                    dataKey="emails" 
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>Service Details</h4>
                <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                  Total: {totalEmails.toLocaleString()} emails
                </span>
              </div>
              
              {services.slice(0, 8).map((service, index) => {
                const percentage = totalEmails > 0 ? (service.email_count / totalEmails * 100) : 0;
                
                return (
                  <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', backgroundColor: '#f9fafb', borderRadius: '0.5rem', transition: 'background-color 0.2s' }}
                       onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                       onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}>
                    <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                      {getServiceIcon(service.service)}
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>
                            {formatServiceName(service.service)}
                          </span>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#111827' }}>
                              {service.email_count.toLocaleString()}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              {percentage.toFixed(1)}% of total
                            </div>
                          </div>
                        </div>
                        
                        {/* Progress bar */}
                        <div style={{ marginTop: '0.5rem', width: '100%', backgroundColor: '#e5e7eb', borderRadius: '9999px', height: '0.375rem' }}>
                          <div 
                            style={{ 
                              height: '0.375rem', 
                              borderRadius: '9999px', 
                              transition: 'all 0.3s',
                              width: `${Math.max(percentage, 2)}%`,
                              backgroundColor: getServiceColor(service.service)
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
              
              {services.length > 8 && (
                <div style={{ textAlign: 'center', paddingTop: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                    And {services.length - 8} more services...
                  </span>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ServiceBreakdown;