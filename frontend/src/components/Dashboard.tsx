import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDomain } from '../contexts/DomainContext';
import { dmarcAPI, DMARCReportSummary, TimeSeriesData } from '../utils/api';
import SummaryCards from './SummaryCards';
import TimeSeriesChart from './TimeSeriesChart';
import ServiceBreakdown from './ServiceBreakdown';
import Header from './Header';
import Navigation from './Navigation';
import UserManagement from './UserManagement';
import AlertsManager from './AlertsManager';
import DNSManager from './DNSManager';
import ConfigurationGuide from './ConfigurationGuide';
import FileUpload from './FileUpload';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { selectedDomain } = useDomain();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [summary, setSummary] = useState<DMARCReportSummary | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [selectedDays, setSelectedDays] = useState(7);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadData();
    }
  }, [selectedDays, activeTab, selectedDomain]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Only load data if a domain is selected
      if (!selectedDomain) {
        setSummary(null);
        setTimeSeriesData([]);
        setIsLoading(false);
        return;
      }
      
      const [summaryData, timeSeriesResult] = await Promise.all([
        dmarcAPI.getSummary(selectedDays, selectedDomain.name),
        dmarcAPI.getTimeSeriesData(selectedDays, selectedDomain.name)
      ]);
      
      setSummary(summaryData);
      setTimeSeriesData(timeSeriesResult);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimeRangeChange = (days: number) => {
    setSelectedDays(days);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return renderDashboardContent();
      case 'users':
        return <UserManagement />;
      case 'alerts':
        return <AlertsManager />;
      case 'dns':
        return <DNSManager />;
      case 'settings':
        return <ConfigurationGuide />;
      case 'upload':
        return (
          <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem 1rem' }}>
            <div style={{ padding: '1.5rem 0' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#111827' }}>Upload DMARC Reports</h1>
                <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6b7280' }}>
                  Upload XML DMARC aggregate reports from your email providers
                </p>
              </div>
              <FileUpload onUploadSuccess={loadData} />
            </div>
          </div>
        );
      default:
        return renderDashboardContent();
    }
  };

  const renderDashboardContent = () => {
    if (!selectedDomain) {
      return (
        <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '16rem' }}>
            <div style={{ fontSize: '1.125rem', fontWeight: '500', color: '#6b7280', marginBottom: '0.5rem' }}>
              No Domain Selected
            </div>
            <div style={{ fontSize: '0.875rem', color: '#9ca3af', textAlign: 'center' }}>
              Please select a domain from the header or add a new domain to start monitoring DMARC data.
            </div>
          </div>
        </div>
      );
    }

    if (isLoading) {
      return (
        <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '16rem' }}>
            <div style={{ 
              animation: 'spin 1s linear infinite', 
              borderRadius: '50%', 
              height: '8rem', 
              width: '8rem', 
              borderBottom: '2px solid #2563eb' 
            }}></div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
          <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '1rem', borderRadius: '0.5rem' }}>
            <p style={{ fontWeight: '500' }}>Error loading dashboard data</p>
            <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>{error}</p>
          </div>
        </div>
      );
    }

    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
        <div style={{ padding: '1.5rem 0' }}>
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
            <div style={{ marginBottom: '1rem' }}>
              <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#111827', marginBottom: '0.25rem' }}>
                DMARC Analytics Dashboard
              </h1>
              <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                Welcome back, {user?.full_name || user?.email}
                {selectedDomain && (
                  <span style={{ marginLeft: '0.5rem', padding: '0.25rem 0.5rem', backgroundColor: '#eff6ff', color: '#2563eb', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: '500' }}>
                    {selectedDomain.name}
                  </span>
                )}
              </p>
            </div>
            
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[7, 30, 90].map((days) => (
                <button
                  key={days}
                  onClick={() => handleTimeRangeChange(days)}
                  style={{
                    padding: '0.75rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: '500',
                    borderRadius: '0.375rem',
                    border: '1px solid #d1d5db',
                    backgroundColor: selectedDays === days ? '#2563eb' : 'white',
                    color: selectedDays === days ? 'white' : '#374151',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (selectedDays !== days) {
                      e.currentTarget.style.backgroundColor = '#f9fafb';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedDays !== days) {
                      e.currentTarget.style.backgroundColor = 'white';
                    }
                  }}
                >
                  {days}d
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {summary && <SummaryCards summary={summary} />}
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
              <TimeSeriesChart data={timeSeriesData} />
              {summary && <ServiceBreakdown services={summary.top_services} />}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb' }}>
      <Header />
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      {renderTabContent()}
    </div>
  );
};

export default Dashboard;