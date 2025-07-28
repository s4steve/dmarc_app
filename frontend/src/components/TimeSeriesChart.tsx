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
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Email Volume Trends
        </h3>
        <div className="h-80">
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