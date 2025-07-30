import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ChartBarIcon, 
  UserGroupIcon, 
  CogIcon, 
  ExclamationTriangleIcon,
  ServerIcon,
  CloudArrowUpIcon,
  ShieldCheckIcon,
  DocumentMagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

const Navigation: React.FC = () => {
  const { user } = useAuth();

  const tabs = [
    { id: '/', name: 'Dashboard', icon: ChartBarIcon },
    { id: '/alerts', name: 'Alerts', icon: ExclamationTriangleIcon },
    { id: '/dns', name: 'DNS Records', icon: ServerIcon },
    { id: '/upload', name: 'Upload', icon: CloudArrowUpIcon },
    { id: '/users', name: 'Users', icon: UserGroupIcon },
    { id: '/settings', name: 'Configuration', icon: CogIcon },
  ];

  if (user?.is_admin) {
    tabs.push({ id: '/dns-scanner', name: 'DNS Scanner', icon: DocumentMagnifyingGlassIcon });
    tabs.push({ id: '/admin', name: 'System Admin', icon: ShieldCheckIcon });
  }

  return (
    <nav style={{ backgroundColor: 'white', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
        <div style={{ display: 'flex', gap: '2rem' }}>
          {tabs.map((tab) => (
            <NavLink
              key={tab.id}
              to={tab.id}
              className={({ isActive }) =>
                `whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center transition-all 
                ${isActive ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`
              }
            >
              <tab.icon className="h-5 w-5 mr-2" />
              {tab.name}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;