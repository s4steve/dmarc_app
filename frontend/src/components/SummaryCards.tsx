import React from 'react';
import { DMARCReportSummary } from '../utils/api';
import { 
  EnvelopeIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ChartBarIcon 
} from '@heroicons/react/24/outline';

interface SummaryCardsProps {
  summary: DMARCReportSummary;
}

const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => {
  const cards = [
    {
      title: 'Total Emails',
      value: summary.total_emails.toLocaleString(),
      icon: EnvelopeIcon,
      iconColor: '#3B82F6', // blue-500
      bgColor: '#EBF8FF', // blue-50
    },
    {
      title: 'Passed Authentication',
      value: summary.passed_emails.toLocaleString(),
      icon: CheckCircleIcon,
      iconColor: '#10B981', // green-500
      bgColor: '#F0FDF4', // green-50
    },
    {
      title: 'Failed Authentication',
      value: summary.failed_emails.toLocaleString(),
      icon: XCircleIcon,
      iconColor: '#EF4444', // red-500
      bgColor: '#FEF2F2', // red-50
    },
    {
      title: 'Pass Rate',
      value: `${summary.pass_rate}%`,
      icon: ChartBarIcon,
      iconColor: summary.pass_rate >= 95 ? '#10B981' : summary.pass_rate >= 80 ? '#F59E0B' : '#EF4444',
      bgColor: summary.pass_rate >= 95 ? '#F0FDF4' : summary.pass_rate >= 80 ? '#FFFBEB' : '#FEF2F2',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <div 
          key={index} 
          className="bg-white shadow rounded-lg p-5"
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div 
                className="p-3 rounded-md"
                style={{ backgroundColor: card.bgColor }}
              >
                <card.icon 
                  className="h-6 w-6"
                  style={{ color: card.iconColor }}
                />
              </div>
            </div>
            <div className="ml-5 flex-1">
              <div>
                <div className="text-sm font-medium text-gray-500 mb-1">
                  {card.title}
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {card.value}
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;