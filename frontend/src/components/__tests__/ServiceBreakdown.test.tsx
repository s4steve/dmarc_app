import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ServiceBreakdown from '../ServiceBreakdown';

// Mock recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

describe('ServiceBreakdown Component', () => {
  const mockServices = [
    { service: 'Google Workspace', email_count: 1000 },
    { service: 'Microsoft 365', email_count: 750 },
    { service: 'Mailchimp', email_count: 500 },
    { service: 'SendGrid', email_count: 250 },
    { service: 'unknown', email_count: 100 }
  ];

  test('renders service breakdown with data', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    expect(screen.getByText('Email Services Breakdown')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  test('renders empty state when no services provided', () => {
    render(<ServiceBreakdown services={[]} />);
    
    expect(screen.getByText('Email Services Breakdown')).toBeInTheDocument();
    expect(screen.getByText('No service data available')).toBeInTheDocument();
    expect(screen.getByText('Upload DMARC reports to see email service breakdown')).toBeInTheDocument();
  });

  test('displays service list with proper inline styling', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    // Check for Google Workspace
    expect(screen.getByText('Google Workspace')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument();
    
    // Check for Microsoft 365
    expect(screen.getByText('Microsoft 365')).toBeInTheDocument();
    expect(screen.getByText('750')).toBeInTheDocument();
  });

  test('shows proper percentage calculations', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    // Total emails = 2600, Google Workspace = 1000, so 38.5%
    expect(screen.getByText('38.5% of total')).toBeInTheDocument();
    
    // Microsoft 365 = 750, so 28.8%
    expect(screen.getByText('28.8% of total')).toBeInTheDocument();
  });

  test('displays total email count correctly', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    // Total should be 1000 + 750 + 500 + 250 + 100 = 2600
    expect(screen.getByText('Total: 2,600 emails')).toBeInTheDocument();
  });

  test('renders service icons with proper styling', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    const container = screen.getByText('Google Workspace').closest('div');
    
    // Check that the parent container has inline styles
    expect(container?.parentElement?.previousElementSibling).toHaveStyle({
      width: '1rem',
      height: '1rem',
      borderRadius: '50%',
      marginRight: '0.75rem'
    });
  });

  test('handles unknown service with question mark icon', () => {
    render(<ServiceBreakdown services={[{ service: 'unknown', email_count: 100 }]} />);
    
    expect(screen.getByText('Unknown Sources')).toBeInTheDocument();
    expect(screen.getByText('?')).toBeInTheDocument();
  });

  test('applies proper hover effects on service items', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    // Find the service item container (the one with onMouseEnter/onMouseLeave)
    const serviceItems = screen.getAllByText(/Google Workspace|Microsoft/);
    const serviceItem = serviceItems[0].closest('[style*="padding: 0.75rem"]');
    
    // Test hover effect
    fireEvent.mouseEnter(serviceItem!);
    expect(serviceItem).toHaveStyle('background-color: rgb(243, 244, 246)');
    
    fireEvent.mouseLeave(serviceItem!);
    expect(serviceItem).toHaveStyle('background-color: rgb(249, 250, 251)');
  });

  test('truncates long service names in chart data', () => {
    const longNameServices = [
      { service: 'Very Long Service Name That Should Be Truncated', email_count: 100 }
    ];
    
    const { container } = render(<ServiceBreakdown services={longNameServices} />);
    
    // The full name should still be displayed in the service list
    expect(screen.getByText('Very Long Service Name That Should Be Truncated')).toBeInTheDocument();
  });

  test('limits display to 8 services maximum', () => {
    const manyServices = Array.from({ length: 12 }, (_, i) => ({
      service: `Service ${i + 1}`,
      email_count: 100 - i
    }));
    
    render(<ServiceBreakdown services={manyServices} />);
    
    // Should show "And X more services..." message
    expect(screen.getByText('And 4 more services...')).toBeInTheDocument();
  });

  test('uses correct brand colors for known services', () => {
    const { container } = render(<ServiceBreakdown services={mockServices} />);
    
    // Check that Google Workspace brand color is present in the DOM
    const googleColorElement = container.querySelector('[style*="#4285F4"], [style*="rgb(66, 133, 244)"]');
    expect(googleColorElement).toBeInTheDocument();
    
    // Check that Microsoft 365 brand color is present
    const microsoftColorElement = container.querySelector('[style*="#FF6B35"], [style*="rgb(255, 107, 53)"]');
    expect(microsoftColorElement).toBeInTheDocument();
  });

  test('applies inline styles instead of CSS classes', () => {
    const { container } = render(<ServiceBreakdown services={mockServices} />);
    
    // Verify no Tailwind classes are present
    const elements = container.querySelectorAll('*');
    elements.forEach(element => {
      const className = element.className;
      expect(className).not.toMatch(/\b(bg-|text-|p-|m-|flex|grid|space-|h-|w-|border|rounded)\b/);
    });
  });

  test('maintains responsive design with inline styles', () => {
    render(<ServiceBreakdown services={mockServices} />);
    
    // Check main container has proper styling
    const mainContainer = screen.getByText('Email Services Breakdown').closest('div')?.parentElement;
    expect(mainContainer).toHaveStyle({
      backgroundColor: 'white',
      overflow: 'hidden',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      borderRadius: '0.5rem'
    });
  });

  test('progress bars are rendered with inline styles', () => {
    const { container } = render(<ServiceBreakdown services={mockServices} />);
    
    // Progress bars are div elements with rounded borders and specific height
    const progressBars = container.querySelectorAll('[style*="border-radius: 9999px"][style*="height: 0.375rem"]');
    expect(progressBars.length).toBeGreaterThan(0);
    
    // Check that each progress bar has a background color
    progressBars.forEach(bar => {
      const style = (bar as HTMLElement).style;
      expect(style.backgroundColor).toBeTruthy();
    });
  });
});