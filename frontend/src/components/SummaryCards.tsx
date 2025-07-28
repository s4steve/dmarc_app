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
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
      {cards.map((card, index) => (
        <div 
          key={index} 
          style={{ 
            backgroundColor: 'white', 
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 
            borderRadius: '0.5rem',
            padding: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ flexShrink: 0 }}>
              <div 
                style={{ 
                  padding: '0.75rem', 
                  borderRadius: '0.375rem',
                  backgroundColor: card.bgColor
                }}
              >
                <card.icon 
                  style={{ 
                    height: '1.5rem', 
                    width: '1.5rem', 
                    color: card.iconColor 
                  }} 
                />
              </div>
            </div>
            <div style={{ marginLeft: '1.25rem', flex: 1 }}>
              <div>
                <div style={{ 
                  fontSize: '0.875rem', 
                  fontWeight: '500', 
                  color: '#6B7280',
                  marginBottom: '0.25rem'
                }}>
                  {card.title}
                </div>
                <div style={{ 
                  fontSize: '1.125rem', 
                  fontWeight: '600', 
                  color: '#111827' 
                }}>
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