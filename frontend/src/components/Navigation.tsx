import React from 'react';
import { 
  ChartBarIcon, 
  UserGroupIcon, 
  CogIcon, 
  ExclamationTriangleIcon,
  ServerIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

interface NavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const Navigation: React.FC<NavigationProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: ChartBarIcon },
    { id: 'alerts', name: 'Alerts', icon: ExclamationTriangleIcon },
    { id: 'dns', name: 'DNS Records', icon: ServerIcon },
    { id: 'upload', name: 'Upload', icon: CloudArrowUpIcon },
    { id: 'users', name: 'Users', icon: UserGroupIcon },
    { id: 'settings', name: 'Configuration', icon: CogIcon },
  ];

  return (
    <nav style={{ backgroundColor: 'white', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
        <div style={{ display: 'flex', gap: '2rem' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              style={{
                whiteSpace: 'nowrap',
                padding: '1rem 0.25rem',
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
        </div>
      </div>
    </nav>
  );
};

export default Navigation;