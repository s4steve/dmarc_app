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
        <div className="w-4 h-4 bg-gray-400 rounded-full flex items-center justify-center mr-3">
          <span className="text-xs text-white font-bold">?</span>
        </div>
      );
    }
    return (
      <div 
        className="w-4 h-4 rounded-full mr-3" 
        style={{ backgroundColor: getServiceColor(serviceName) }}
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
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Email Services Breakdown
        </h3>
        
        {services.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm">No service data available</p>
            <p className="text-gray-400 text-xs mt-1">Upload DMARC reports to see email service breakdown</p>
          </div>
        ) : (
          <>
            <div className="h-64 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
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
            
            <div className="space-y-3">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-sm font-medium text-gray-700">Service Details</h4>
                <span className="text-xs text-gray-500">
                  Total: {totalEmails.toLocaleString()} emails
                </span>
              </div>
              
              {services.slice(0, 8).map((service, index) => {
                const percentage = totalEmails > 0 ? (service.email_count / totalEmails * 100) : 0;
                
                return (
                  <div key={index} className="flex justify-between items-center py-3 px-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center flex-1">
                      {getServiceIcon(service.service)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900">
                            {formatServiceName(service.service)}
                          </span>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-gray-900">
                              {service.email_count.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500">
                              {percentage.toFixed(1)}% of total
                            </div>
                          </div>
                        </div>
                        
                        {/* Progress bar */}
                        <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
                          <div 
                            className="h-1.5 rounded-full transition-all duration-300"
                            style={{ 
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
                <div className="text-center pt-2">
                  <span className="text-xs text-gray-500">
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