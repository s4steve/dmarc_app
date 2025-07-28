import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AuthContext } from '../../contexts/AuthContext';
import { DomainContext } from '../../contexts/DomainContext';
import Dashboard from '../../components/Dashboard';
import * as api from '../../utils/api';

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />
}));

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  EnvelopeIcon: (props: any) => <div data-testid="envelope-icon" style={props.style} />,
  CheckCircleIcon: (props: any) => <div data-testid="check-circle-icon" style={props.style} />,
  XCircleIcon: (props: any) => <div data-testid="x-circle-icon" style={props.style} />,
  ChartBarIcon: (props: any) => <div data-testid="chart-bar-icon" style={props.style} />,
  UserCircleIcon: (props: any) => <div data-testid="user-circle-icon" style={props.style} />,
  ArrowRightOnRectangleIcon: (props: any) => <div data-testid="logout-icon" style={props.style} />,
  ShieldCheckIcon: (props: any) => <div data-testid="shield-check-icon" style={props.style} />,
  PlusIcon: (props: any) => <div data-testid="plus-icon" style={props.style} />,
  ChevronDownIcon: (props: any) => <div data-testid="chevron-down-icon" style={props.style} />,
  UserGroupIcon: (props: any) => <div data-testid="user-group-icon" style={props.style} />,
  CogIcon: (props: any) => <div data-testid="cog-icon" style={props.style} />,
  ExclamationTriangleIcon: (props: any) => <div data-testid="exclamation-triangle-icon" style={props.style} />,
  ServerIcon: (props: any) => <div data-testid="server-icon" style={props.style} />,
  CloudArrowUpIcon: (props: any) => <div data-testid="cloud-arrow-up-icon" style={props.style} />
}));

// Mock Headless UI
jest.mock('@headlessui/react', () => ({
  Menu: {
    Button: ({ children, style, onMouseEnter, onMouseLeave, ...props }: any) => (
      <button style={style} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} {...props}>
        {children}
      </button>
    ),
    Items: ({ children, style }: any) => <div style={style}>{children}</div>,
    Item: ({ children }: any) => <div>{children({ active: false })}</div>
  },
  Transition: ({ children }: any) => <div>{children}</div>
}));

// Mock child components that we don't need for integration testing
jest.mock('../../components/UserManagement', () => {
  return function MockUserManagement() {
    return <div data-testid="user-management">User Management Component</div>;
  };
});

jest.mock('../../components/AlertsManager', () => {
  return function MockAlertsManager() {
    return <div data-testid="alerts-manager">Alerts Manager Component</div>;
  };
});

jest.mock('../../components/DNSManager', () => {
  return function MockDNSManager() {
    return <div data-testid="dns-manager">DNS Manager Component</div>;
  };
});

jest.mock('../../components/ConfigurationGuide', () => {
  return function MockConfigurationGuide() {
    return <div data-testid="configuration-guide">Configuration Guide Component</div>;
  };
});

jest.mock('../../components/FileUpload', () => {
  return function MockFileUpload({ onUploadSuccess }: any) {
    return (
      <div data-testid="file-upload">
        <button onClick={() => onUploadSuccess()}>Test Upload</button>
      </div>
    );
  };
});

jest.mock('../../components/AddDomainModal', () => {
  return function MockAddDomainModal({ isOpen, onClose }: any) {
    return isOpen ? (
      <div data-testid="add-domain-modal">
        <button onClick={onClose}>Close Modal</button>
      </div>
    ) : null;
  };
});

// Mock API
jest.mock('../../utils/api', () => ({
  dmarcAPI: {
    getSummary: jest.fn(),
    getTimeSeriesData: jest.fn(),
  },
}));

const mockUser = {
  id: 'user-1',
  email: 'admin@example.com',
  full_name: 'Admin User',
  role: 'system_admin',
  customer_id: 'default',
  is_active: true,
  created_at: '2025-07-28T00:00:00Z',
  updated_at: '2025-07-28T00:00:00Z'
};

const mockDomains = [
  {
    id: 'domain-1',
    name: 'example.com',
    customer_id: 'default',
    created_at: '2025-07-28T00:00:00Z'
  },
  {
    id: 'domain-2', 
    name: 'test.com',
    customer_id: 'default',
    created_at: '2025-07-28T00:00:00Z'
  }
];

const mockSummaryData = {
  total_emails: 10000,
  passed_emails: 9200,
  failed_emails: 800,
  pass_rate: 92,
  top_services: [
    { service: 'Google Workspace', email_count: 4000 },
    { service: 'Microsoft 365', email_count: 3500 },
    { service: 'Mailchimp', email_count: 1500 },
    { service: 'SendGrid', email_count: 800 },
    { service: 'Amazon SES', email_count: 200 }
  ]
};

const mockTimeSeriesData = [
  { date: '2025-07-21', total_emails: 1200, passed_emails: 1100, failed_emails: 100, pass_rate: 92 },
  { date: '2025-07-22', total_emails: 1400, passed_emails: 1300, failed_emails: 100, pass_rate: 93 },
  { date: '2025-07-23', total_emails: 1600, passed_emails: 1480, failed_emails: 120, pass_rate: 92.5 },
  { date: '2025-07-24', total_emails: 1300, passed_emails: 1200, failed_emails: 100, pass_rate: 92 },
  { date: '2025-07-25', total_emails: 1500, passed_emails: 1380, failed_emails: 120, pass_rate: 92 },
  { date: '2025-07-26', total_emails: 1700, passed_emails: 1564, failed_emails: 136, pass_rate: 92 },
  { date: '2025-07-27', total_emails: 1300, passed_emails: 1196, failed_emails: 104, pass_rate: 92 }
];

const renderFullDashboard = (authOverrides = {}, domainOverrides = {}) => {
  const authValue = {
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: jest.fn(),
    logout: jest.fn(),
    ...authOverrides
  };

  const domainValue = {
    domains: mockDomains,
    selectedDomain: mockDomains[0],
    setSelectedDomain: jest.fn(),
    addDomain: jest.fn(),
    ...domainOverrides
  };

  return render(
    <AuthContext.Provider value={authValue}>
      <DomainContext.Provider value={domainValue}>
        <Dashboard />
      </DomainContext.Provider>
    </AuthContext.Provider>
  );
};

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.dmarcAPI.getSummary as jest.Mock).mockResolvedValue(mockSummaryData);
    (api.dmarcAPI.getTimeSeriesData as jest.Mock).mockResolvedValue(mockTimeSeriesData);
  });

  describe('Full Dashboard Rendering with Real Data', () => {
    test('renders complete dashboard with all components and data', async () => {
      renderFullDashboard();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
      });

      // Check all main sections are present
      expect(screen.getByText('Welcome back, Admin User')).toBeInTheDocument();
      expect(screen.getByText('example.com')).toBeInTheDocument();
      
      // Check summary cards
      expect(screen.getByText('Total Emails')).toBeInTheDocument();
      expect(screen.getByText('10,000')).toBeInTheDocument();
      expect(screen.getByText('Passed Authentication')).toBeInTheDocument();
      expect(screen.getByText('9,200')).toBeInTheDocument();
      expect(screen.getByText('Failed Authentication')).toBeInTheDocument();
      expect(screen.getByText('800')).toBeInTheDocument();
      expect(screen.getByText('Pass Rate')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();

      // Check service breakdown
      expect(screen.getByText('Email Services Breakdown')).toBeInTheDocument();
      expect(screen.getByText('Google Workspace')).toBeInTheDocument();
      expect(screen.getByText('4,000')).toBeInTheDocument();
      expect(screen.getByText('Microsoft 365')).toBeInTheDocument();
      expect(screen.getByText('3,500')).toBeInTheDocument();

      // Check time series chart
      expect(screen.getByText('Email Volume Trends')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });

    test('all components use inline styles without CSS classes', async () => {
      const { container } = renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
      });

      // Check that no elements use Tailwind classes
      const elements = container.querySelectorAll('*');
      elements.forEach(element => {
        const className = element.className;
        if (className) {
          expect(className).not.toMatch(/\b(bg-|text-|p-|m-|flex|grid|space-|h-|w-|border|rounded|min-h)\b/);
        }
      });

      // Verify inline styles are present on key elements
      const mainContainer = container.querySelector('[style*="min-height: 100vh"]');
      expect(mainContainer).toHaveStyle({
        minHeight: '100vh',
        backgroundColor: '#f9fafb'
      });
    });

    test('service breakdown displays proper percentages and colors', async () => {
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('Google Workspace')).toBeInTheDocument();
      });

      // Check percentage calculations (Google Workspace: 4000/10000 = 40%)
      expect(screen.getByText('40.0% of total')).toBeInTheDocument();
      
      // Check Microsoft 365 (3500/10000 = 35%)
      expect(screen.getByText('35.0% of total')).toBeInTheDocument();

      // Check total display
      expect(screen.getByText('Total: 10,000 emails')).toBeInTheDocument();
    });

    test('time range buttons work correctly with API calls', async () => {
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('7d')).toBeInTheDocument();
      });

      // Initially loads 7 days
      expect(api.dmarcAPI.getSummary).toHaveBeenCalledWith(7, 'example.com');
      expect(api.dmarcAPI.getTimeSeriesData).toHaveBeenCalledWith(7, 'example.com');

      // Click 30 day button
      const thirtyDayButton = screen.getByText('30d');
      fireEvent.click(thirtyDayButton);

      await waitFor(() => {
        expect(api.dmarcAPI.getSummary).toHaveBeenCalledWith(30, 'example.com');
        expect(api.dmarcAPI.getTimeSeriesData).toHaveBeenCalledWith(30, 'example.com');
      });
    });

    test('navigation between tabs works correctly', async () => {
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
      });

      // Click Users tab
      const usersTab = screen.getByText('Users').closest('button');
      fireEvent.click(usersTab!);

      await waitFor(() => {
        expect(screen.getByTestId('user-management')).toBeInTheDocument();
      });

      // Click Upload tab
      const uploadTab = screen.getByText('Upload').closest('button');
      fireEvent.click(uploadTab!);

      await waitFor(() => {
        expect(screen.getByText('Upload DMARC Reports')).toBeInTheDocument();
        expect(screen.getByTestId('file-upload')).toBeInTheDocument();
      });

      // Return to Dashboard
      const dashboardTab = screen.getByText('Dashboard').closest('button');
      fireEvent.click(dashboardTab!);

      await waitFor(() => {
        expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
      });
    });

    test('handles no domain selected state', async () => {
      renderFullDashboard({}, { selectedDomain: null });

      await waitFor(() => {
        expect(screen.getByText('No Domain Selected')).toBeInTheDocument();
      });

      expect(screen.getByText('Please select a domain from the header or add a new domain to start monitoring DMARC data.')).toBeInTheDocument();

      // Should not make API calls when no domain selected
      expect(api.dmarcAPI.getSummary).not.toHaveBeenCalled();
      expect(api.dmarcAPI.getTimeSeriesData).not.toHaveBeenCalled();
    });

    test('handles API errors gracefully', async () => {
      (api.dmarcAPI.getSummary as jest.Mock).mockRejectedValue(new Error('Network error'));
      
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('Error loading dashboard data')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      const errorContainer = screen.getByText('Error loading dashboard data').closest('div');
      expect(errorContainer).toHaveStyle({
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        color: '#dc2626'
      });
    });

    test('file upload triggers data refresh', async () => {
      renderFullDashboard();

      // Navigate to upload tab
      const uploadTab = screen.getByText('Upload').closest('button');
      fireEvent.click(uploadTab!);

      await waitFor(() => {
        expect(screen.getByTestId('file-upload')).toBeInTheDocument();
      });

      // Clear previous calls
      jest.clearAllMocks();
      (api.dmarcAPI.getSummary as jest.Mock).mockResolvedValue(mockSummaryData);
      (api.dmarcAPI.getTimeSeriesData as jest.Mock).mockResolvedValue(mockTimeSeriesData);

      // Trigger upload
      const uploadButton = screen.getByText('Test Upload');
      fireEvent.click(uploadButton);

      // Should reload data
      await waitFor(() => {
        expect(api.dmarcAPI.getSummary).toHaveBeenCalledWith(7, 'example.com');
        expect(api.dmarcAPI.getTimeSeriesData).toHaveBeenCalledWith(7, 'example.com');
      });
    });

    test('responsive grid layout works correctly', async () => {
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('DMARC Analytics Dashboard')).toBeInTheDocument();
      });

      // Check summary cards grid
      const summaryContainer = screen.getByText('Total Emails').closest('div')?.parentElement;
      expect(summaryContainer).toHaveStyle({
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1.5rem'
      });

      // Check main content grid
      const chartContainer = screen.getByText('Email Volume Trends').closest('div')?.parentElement;
      expect(chartContainer).toHaveStyle({
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '1.5rem'
      });
    });

    test('service icons have consistent sizing', async () => {
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByText('Google Workspace')).toBeInTheDocument();
      });

      // All service icons should be consistently sized
      const serviceItems = screen.getAllByText(/Google Workspace|Microsoft 365|Mailchimp/);
      
      serviceItems.forEach(item => {
        const iconContainer = item.closest('div')?.previousElementSibling;
        expect(iconContainer).toHaveStyle({
          width: '1rem',
          height: '1rem',
          borderRadius: '50%'
        });
      });
    });

    test('header and navigation are properly styled', async () => {
      renderFullDashboard();

      await waitFor(() => {
        expect(screen.getByTestId('shield-check-icon')).toBeInTheDocument();
      });

      // Check logo icon sizing
      const logoIcon = screen.getByTestId('shield-check-icon');
      expect(logoIcon).toHaveStyle({
        height: '2rem',
        width: '2rem',
        color: '#2563EB'
      });

      // Check navigation icons
      const navIcons = [
        screen.getByTestId('exclamation-triangle-icon'),
        screen.getByTestId('server-icon'),
        screen.getByTestId('cloud-arrow-up-icon'),
        screen.getByTestId('user-group-icon'),
        screen.getByTestId('cog-icon')
      ];

      navIcons.forEach(icon => {
        expect(icon).toHaveStyle({
          height: '1rem',
          width: '1rem'
        });
      });
    });
  });
});