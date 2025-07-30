import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './Header';
import Navigation from './Navigation';
import DashboardContent from './DashboardContent';
import UserManagement from './UserManagement';
import AlertsManager from './AlertsManager';
import DNSManager from './DNSManager';
import ConfigurationGuide from './ConfigurationGuide';
import FileUpload from './FileUpload';
import AdminInterface from './AdminInterface';
import DNSScanner from './DNSScanner';

const Dashboard: React.FC = () => {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <Header />
      <Navigation />
      <Routes>
        <Route path="/" element={<DashboardContent />} />
        <Route path="/users" element={<UserManagement />} />
        <Route path="/alerts" element={<AlertsManager />} />
        <Route path="/dns" element={<DNSManager />} />
        <Route path="/settings" element={<ConfigurationGuide />} />
        <Route path="/upload" element={<FileUpload />} />
        <Route path="/admin" element={<AdminInterface />} />
        <Route path="/dns-scanner" element={<DNSScanner />} />
      </Routes>
    </div>
  );
};

export default Dashboard;