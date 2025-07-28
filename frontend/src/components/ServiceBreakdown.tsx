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
  const chartData = services.map(service => ({
    name: service.service,
    emails: service.email_count,
  }));

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Top Email Services
        </h3>
        
        {services.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No service data available</p>
          </div>
        ) : (
          <>
            <div className="h-64 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value: any) => [value.toLocaleString(), 'Emails']}
                    labelFormatter={(label) => `Service: ${label}`}
                  />
                  <Bar dataKey="emails" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            <div className="space-y-2">
              {services.slice(0, 5).map((service, index) => (
                <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                    <span className="text-sm font-medium text-gray-900">
                      {service.service}
                    </span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {service.email_count.toLocaleString()} emails
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ServiceBreakdown;