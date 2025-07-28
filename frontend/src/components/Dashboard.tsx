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
          <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div className="px-4 py-6 sm:px-0">
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Upload DMARC Reports</h1>
                <p className="mt-1 text-sm text-gray-600">
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-center h-64">
            <div className="text-lg font-medium text-gray-500 mb-2">
              No Domain Selected
            </div>
            <div className="text-sm text-gray-400 text-center">
              Please select a domain from the header or add a new domain to start monitoring DMARC data.
            </div>
          </div>
        </div>
      );
    }

    if (isLoading) {
      return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <p className="font-medium">Error loading dashboard data</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      );
    }

    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
            <div className="mb-4 sm:mb-0">
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                DMARC Analytics Dashboard
              </h1>
              <p className="text-sm text-gray-600">
                Welcome back, {user?.full_name || user?.email}
                {selectedDomain && (
                  <span className="ml-2 px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                    {selectedDomain.name}
                  </span>
                )}
              </p>
            </div>
            
            <div className="flex space-x-2">
              {[7, 30, 90].map((days) => (
                <button
                  key={days}
                  onClick={() => handleTimeRangeChange(days)}
                  className={`px-3 py-2 text-sm font-medium rounded-md border transition-colors ${
                    selectedDays === days
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {days}d
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            {summary && <SummaryCards summary={summary} />}
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <TimeSeriesChart data={timeSeriesData} />
              {summary && <ServiceBreakdown services={summary.top_services} />}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
      {renderTabContent()}
    </div>
  );
};

export default Dashboard;