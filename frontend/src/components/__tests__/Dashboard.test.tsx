import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from '../Dashboard';
import { AuthContext } from '../../contexts/AuthContext';
import { DomainContext } from '../../contexts/DomainContext';
import * as api from '../../utils/api';

// Mock the API calls
jest.mock('../../utils/api', () => ({
  dmarcAPI: {
    getSummary: jest.fn(),
    getTimeSeriesData: jest.fn(),
  },
}));

// Mock child components
jest.mock('../SummaryCards', () => {
  return function MockSummaryCards({ summary }: any) {
    return <div data-testid="summary-cards">Summary Cards - {summary?.total_emails || 0} emails</div>;
  };
});

jest.mock('../TimeSeriesChart', () => {
  return function MockTimeSeriesChart({ data }: any) {
    return <div data-testid="time-series-chart">Time Series Chart - {data?.length || 0} data points</div>;
  };
});

jest.mock('../ServiceBreakdown', () => {
  return function MockServiceBreakdown({ services }: any) {
    return <div data-testid="service-breakdown">Service Breakdown - {services?.length || 0} services</div>;
  };
});

jest.mock('../Header', () => {
  return function MockHeader() {
    return <div data-testid="header">Header</div>;
  };
});

jest.mock('../Navigation', () => {
  return function MockNavigation({ activeTab, onTabChange }: any) {
    return (
      <div data-testid="navigation">
        <button onClick={() => onTabChange('dashboard')}>Dashboard</button>
        <button onClick={() => onTabChange('users')}>Users</button>
        <button onClick={() => onTabChange('upload')}>Upload</button>
      </div>
    );
  };
});

jest.mock('../UserManagement', () => {
  return function MockUserManagement() {
    return <div data-testid="user-management">User Management</div>;
  };
});

jest.mock('../FileUpload', () => {
  return function MockFileUpload({ onUploadSuccess }: any) {
    return (
      <div data-testid="file-upload">
        <button onClick={() => onUploadSuccess()}>Upload File</button>
      </div>
    );
  };
});

const mockUser = {
  id: 'test-user',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'admin',
  customer_id: 'test-customer',
  is_active: true,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z'
};

const mockDomain = {
  id: 'test-domain',
  name: 'example.com',
  customer_id: 'test-customer',
  created_at: '2025-01-01T00:00:00Z'
};

const mockSummary = {
  total_emails: 1000,
  passed_emails: 950,
  failed_emails: 50,
  pass_rate: 95,
  top_services: [
    { service: 'Google Workspace', email_count: 500 },
    { service: 'Microsoft 365', email_count: 300 }
  ]
};

const mockTimeSeriesData = [
  { date: '2025-07-25', total_emails: 100, passed_emails: 95, failed_emails: 5, pass_rate: 95 },
  { date: '2025-07-26', total_emails: 120, passed_emails: 110, failed_emails: 10, pass_rate: 92 }
];

const renderDashboard = (authValue: any = {}, domainValue: any = {}) => {
  const defaultAuthValue = {
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: jest.fn(),
    logout: jest.fn(),
    ...authValue
  };

  const defaultDomainValue = {
    domains: [mockDomain],
    selectedDomain: mockDomain,
    setSelectedDomain: jest.fn(),
    addDomain: jest.fn(),
    ...domainValue
  };

  return render(
    <AuthContext.Provider value={defaultAuthValue}>
      <DomainContext.Provider value={defaultDomainValue}>
        <Dashboard />
      </DomainContext.Provider>
    </AuthContext.Provider>
  );
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.dmarcAPI.getSummary as jest.Mock).mockResolvedValue(mockSummary);
    (api.dmarcAPI.getTimeSeriesData as jest.Mock).mockResolvedValue(mockTimeSeriesData);
  });

  test('renders dashboard with all components', async () => {
    renderDashboard();

    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('navigation')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
    });
  });

  test('applies inline styles instead of Tailwind classes', () => {
    const { container } = renderDashboard();
    
    // Check main container has inline styles
    const mainContainer = container.querySelector('div[style*="min-height: 100vh"]');
    expect(mainContainer).toHaveStyle({
      minHeight: '100vh',
      backgroundColor: '#f9fafb'
    });
  });

  test('displays user greeting with inline styling', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText(/Welcome back, Test User/)).toBeInTheDocument();
    });
    
    const greeting = screen.getByText(/Test User/);
    expect(greeting).toHaveStyle({
      fontSize: '0.875rem',
      color: '#6b7280'
    });
  });

  test('shows domain badge with proper styling', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByText('example.com')).toBeInTheDocument();
    });
    
    const domainBadge = screen.getByText('example.com');
    expect(domainBadge).toHaveStyle({
      marginLeft: '0.5rem',
      padding: '0.25rem 0.5rem',
      backgroundColor: '#eff6ff',
      color: '#2563eb',
      borderRadius: '0.25rem',
      fontSize: '0.75rem',
      fontWeight: '500'
    });
  });

  test('renders time range buttons with inline styles', async () => {
    renderDashboard();
    
    await waitFor(() => {
      const timeButtons = screen.getAllByText(/\d+d/);
      expect(timeButtons).toHaveLength(3);
      
      timeButtons.forEach(button => {
        expect(button).toHaveStyle({
          padding: '0.75rem 1rem',
          fontSize: '0.875rem',
          fontWeight: '500',
          borderRadius: '0.375rem',
          border: '1px solid #d1d5db',
          cursor: 'pointer'
        });
      });
    });
  });

  test('handles time range selection with proper styling updates', async () => {
    renderDashboard();
    
    await waitFor(() => {
      const sevenDayButton = screen.getByText('7d');
      const thirtyDayButton = screen.getByText('30d');
      
      // Initial state - 7d should be selected
      expect(sevenDayButton).toHaveStyle({
        backgroundColor: '#2563eb',
        color: 'white'
      });
      
      expect(thirtyDayButton).toHaveStyle({
        backgroundColor: 'white',
        color: '#374151'
      });
      
      // Click 30d button
      fireEvent.click(thirtyDayButton);
      
      // After click - 30d should be selected
      expect(thirtyDayButton).toHaveStyle({
        backgroundColor: '#2563eb',
        color: 'white'
      });
    });
  });

  test('displays no domain selected state with proper styling', () => {
    renderDashboard({}, { selectedDomain: null });
    
    const noDomainContainer = screen.getByText('No Domain Selected').closest('div');
    expect(noDomainContainer).toHaveStyle({
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '16rem'
    });
    
    const title = screen.getByText('No Domain Selected');
    expect(title).toHaveStyle({
      fontSize: '1.125rem',
      fontWeight: '500',
      color: '#6b7280',
      marginBottom: '0.5rem'
    });
  });

  test('shows loading state with proper spinner styling', () => {
    renderDashboard();
    
    // Initially shows loading
    const spinner = screen.getByRole('progressbar', { hidden: true });
    expect(spinner).toHaveStyle({
      animation: 'spin 1s linear infinite',
      borderRadius: '50%',
      height: '8rem',
      width: '8rem',
      borderBottom: '2px solid #2563eb'
    });
  });

  test('displays error state with proper styling', async () => {
    (api.dmarcAPI.getSummary as jest.Mock).mockRejectedValue(new Error('API Error'));
    
    renderDashboard();
    
    await waitFor(() => {
      const errorContainer = screen.getByText('Error loading dashboard data').closest('div');
      expect(errorContainer).toHaveStyle({
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        color: '#dc2626',
        padding: '1rem',
        borderRadius: '0.5rem'
      });
    });
  });

  test('loads and displays dashboard data correctly', async () => {
    renderDashboard();
    
    await waitFor(() => {
      expect(screen.getByTestId('summary-cards')).toBeInTheDocument();
      expect(screen.getByTestId('time-series-chart')).toBeInTheDocument();
      expect(screen.getByTestId('service-breakdown')).toBeInTheDocument();
    });
    
    expect(api.dmarcAPI.getSummary).toHaveBeenCalledWith(7, 'example.com');
    expect(api.dmarcAPI.getTimeSeriesData).toHaveBeenCalledWith(7, 'example.com');
  });

  test('switches to users tab correctly', async () => {
    renderDashboard();
    
    const usersButton = screen.getByText('Users');
    fireEvent.click(usersButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('user-management')).toBeInTheDocument();
    });
  });

  test('displays upload tab with proper inline styling', async () => {
    renderDashboard();
    
    const uploadButton = screen.getByText('Upload');
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      expect(screen.getByText('Upload DMARC Reports')).toBeInTheDocument();
      expect(screen.getByTestId('file-upload')).toBeInTheDocument();
    });
    
    const uploadTitle = screen.getByText('Upload DMARC Reports');
    expect(uploadTitle).toHaveStyle({
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: '#111827'
    });
    
    const uploadDescription = screen.getByText('Upload XML DMARC aggregate reports from your email providers');
    expect(uploadDescription).toHaveStyle({
      marginTop: '0.25rem',
      fontSize: '0.875rem',
      color: '#6b7280'
    });
  });

  test('handles successful file upload and reloads data', async () => {
    renderDashboard();
    
    const uploadButton = screen.getByText('Upload');
    fireEvent.click(uploadButton);
    
    await waitFor(() => {
      const fileUploadButton = screen.getByText('Upload File');
      fireEvent.click(fileUploadButton);
    });
    
    // Should reload data after upload
    expect(api.dmarcAPI.getSummary).toHaveBeenCalledTimes(2);
  });

  test('grid layout uses proper inline styles', async () => {
    renderDashboard();
    
    await waitFor(() => {
      const gridContainer = screen.getByTestId('summary-cards').parentElement?.nextElementSibling;
      expect(gridContainer).toHaveStyle({
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '1.5rem'
      });
    });
  });

  test('does not use any CSS classes - only inline styles', async () => {
    const { container } = renderDashboard();
    
    await waitFor(() => {
      // Wait for content to load
      expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
    });
    
    // Verify no Tailwind or other CSS classes are present
    const elements = container.querySelectorAll('*');
    elements.forEach(element => {
      const className = element.className;
      if (className) {
        // Allow test-related classes but not styling classes
        expect(className).not.toMatch(/\b(bg-|text-|p-|m-|flex|grid|space-|h-|w-|border|rounded|min-h)\b/);
      }
    });
  });

  test('button hover effects work with inline styles', async () => {
    renderDashboard();
    
    await waitFor(() => {
      const thirtyDayButton = screen.getByText('30d');
      
      // Test hover effect
      fireEvent.mouseEnter(thirtyDayButton);
      expect(thirtyDayButton).toHaveStyle('backgroundColor: #f9fafb');
      
      fireEvent.mouseLeave(thirtyDayButton);
      expect(thirtyDayButton).toHaveStyle('backgroundColor: white');
    });
  });
});