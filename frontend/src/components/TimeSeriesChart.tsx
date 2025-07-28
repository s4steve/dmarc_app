import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TimeSeriesData } from '../utils/api';

interface TimeSeriesChartProps {
  data: TimeSeriesData[];
}

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ data }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const chartData = data.map(item => ({
    ...item,
    date: formatDate(item.date),
  }));

  return (
    <div style={{ backgroundColor: 'white', overflow: 'hidden', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderRadius: '0.5rem' }}>
      <div style={{ padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1.125rem', lineHeight: '1.75rem', fontWeight: '500', color: '#111827', marginBottom: '1rem' }}>
          Email Volume Trends
        </h3>
        <div style={{ height: '20rem' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                labelFormatter={(label) => `Date: ${label}`}
                formatter={(value: any, name: string) => [
                  typeof value === 'number' ? value.toLocaleString() : value,
                  name === 'total_emails' ? 'Total Emails' :
                  name === 'passed_emails' ? 'Passed' :
                  name === 'failed_emails' ? 'Failed' :
                  name === 'pass_rate' ? 'Pass Rate (%)' : name
                ]}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="total_emails"
                stroke="#3B82F6"
                strokeWidth={2}
                name="Total Emails"
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="passed_emails"
                stroke="#10B981"
                strokeWidth={2}
                name="Passed"
                dot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="failed_emails"
                stroke="#EF4444"
                strokeWidth={2}
                name="Failed"
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default TimeSeriesChart;