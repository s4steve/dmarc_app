import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SummaryCards from '../SummaryCards';
import { DMARCReportSummary } from '../../utils/api';

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  EnvelopeIcon: () => <div data-testid="envelope-icon" />,
  CheckCircleIcon: () => <div data-testid="check-circle-icon" />,
  XCircleIcon: () => <div data-testid="x-circle-icon" />,
  ChartBarIcon: () => <div data-testid="chart-bar-icon" />,
}));

describe('SummaryCards Component', () => {
  const mockSummary: DMARCReportSummary = {
    total_emails: 10000,
    passed_emails: 9500,
    failed_emails: 500,
    pass_rate: 95,
    top_services: []
  };

  test('renders all summary cards with correct data', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    expect(screen.getByText('Total Emails')).toBeInTheDocument();
    expect(screen.getByText('10,000')).toBeInTheDocument();
    
    expect(screen.getByText('Passed Authentication')).toBeInTheDocument();
    expect(screen.getByText('9,500')).toBeInTheDocument();
    
    expect(screen.getByText('Failed Authentication')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
    
    expect(screen.getByText('Pass Rate')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  test('displays proper icons for each metric', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    expect(screen.getByTestId('envelope-icon')).toBeInTheDocument();
    expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument();
    expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument();
    expect(screen.getByTestId('chart-bar-icon')).toBeInTheDocument();
  });

  test('applies correct colors based on pass rate - excellent (>= 95%)', () => {
    const excellentSummary = { ...mockSummary, pass_rate: 98 };
    render(<SummaryCards summary={excellentSummary} />);
    
    const passRateIcon = screen.getByTestId('chart-bar-icon');
    expect(passRateIcon).toHaveStyle('color: #10B981'); // green
    
    const passRateContainer = passRateIcon.closest('div');
    expect(passRateContainer).toHaveStyle('background-color: #F0FDF4'); // green bg
  });

  test('applies correct colors based on pass rate - good (>= 80%)', () => {
    const goodSummary = { ...mockSummary, pass_rate: 85 };
    render(<SummaryCards summary={goodSummary} />);
    
    const passRateIcon = screen.getByTestId('chart-bar-icon');
    expect(passRateIcon).toHaveStyle('color: #F59E0B'); // amber
    
    const passRateContainer = passRateIcon.closest('div');
    expect(passRateContainer).toHaveStyle('background-color: #FFFBEB'); // amber bg
  });

  test('applies correct colors based on pass rate - poor (< 80%)', () => {
    const poorSummary = { ...mockSummary, pass_rate: 65 };
    render(<SummaryCards summary={poorSummary} />);
    
    const passRateIcon = screen.getByTestId('chart-bar-icon');
    expect(passRateIcon).toHaveStyle('color: #EF4444'); // red
    
    const passRateContainer = passRateIcon.closest('div');
    expect(passRateContainer).toHaveStyle('background-color: #FEF2F2'); // red bg
  });

  test('uses grid layout with inline styles', () => {
    const { container } = render(<SummaryCards summary={mockSummary} />);
    
    const gridContainer = container.firstChild;
    expect(gridContainer).toHaveStyle({
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '1.5rem'
    });
  });

  test('card containers have proper styling', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    const cards = screen.getAllByText(/Total Emails|Passed Authentication|Failed Authentication|Pass Rate/).map(
      text => text.closest('div')?.parentElement
    );
    
    cards.forEach(card => {
      expect(card).toHaveStyle({
        backgroundColor: 'white',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        borderRadius: '0.5rem',
        padding: '1.25rem'
      });
    });
  });

  test('icon containers have correct styling', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    const iconContainers = [
      screen.getByTestId('envelope-icon').closest('div'),
      screen.getByTestId('check-circle-icon').closest('div'),
      screen.getByTestId('x-circle-icon').closest('div'),
      screen.getByTestId('chart-bar-icon').closest('div')
    ];
    
    iconContainers.forEach(container => {
      expect(container).toHaveStyle({
        padding: '0.75rem',
        borderRadius: '0.375rem'
      });
    });
  });

  test('icons have consistent sizing', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    const icons = [
      screen.getByTestId('envelope-icon'),
      screen.getByTestId('check-circle-icon'),
      screen.getByTestId('x-circle-icon'),
      screen.getByTestId('chart-bar-icon')
    ];
    
    icons.forEach(icon => {
      expect(icon).toHaveStyle({
        height: '1.5rem',
        width: '1.5rem'
      });
    });
  });

  test('handles large numbers with proper formatting', () => {
    const largeSummary: DMARCReportSummary = {
      total_emails: 1234567,
      passed_emails: 1200000,
      failed_emails: 34567,
      pass_rate: 97,
      top_services: []
    };
    
    render(<SummaryCards summary={largeSummary} />);
    
    expect(screen.getByText('1,234,567')).toBeInTheDocument();
    expect(screen.getByText('1,200,000')).toBeInTheDocument();
    expect(screen.getByText('34,567')).toBeInTheDocument();
  });

  test('handles zero values correctly', () => {
    const zeroSummary: DMARCReportSummary = {
      total_emails: 0,
      passed_emails: 0,
      failed_emails: 0,
      pass_rate: 0,
      top_services: []
    };
    
    render(<SummaryCards summary={zeroSummary} />);
    
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  test('applies proper brand colors for different metrics', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    // Total Emails - Blue
    const totalEmailsIcon = screen.getByTestId('envelope-icon');
    expect(totalEmailsIcon).toHaveStyle('color: #3B82F6');
    
    // Passed Authentication - Green
    const passedIcon = screen.getByTestId('check-circle-icon');
    expect(passedIcon).toHaveStyle('color: #10B981');
    
    // Failed Authentication - Red
    const failedIcon = screen.getByTestId('x-circle-icon');
    expect(failedIcon).toHaveStyle('color: #EF4444');
  });

  test('does not use any CSS classes - only inline styles', () => {
    const { container } = render(<SummaryCards summary={mockSummary} />);
    
    // Verify no Tailwind or other CSS classes are present
    const elements = container.querySelectorAll('*');
    elements.forEach(element => {
      const className = element.className;
      expect(className).not.toMatch(/\b(bg-|text-|p-|m-|flex|grid|space-|h-|w-|border|rounded)\b/);
    });
  });

  test('typography has proper styling', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    // Check title styling
    const titles = screen.getAllByText(/Total Emails|Passed Authentication|Failed Authentication|Pass Rate/);
    titles.forEach(title => {
      expect(title).toHaveStyle({
        fontSize: '0.875rem',
        fontWeight: '500',
        color: '#6B7280'
      });
    });
    
    // Check value styling
    const values = screen.getAllByText(/10,000|9,500|500|95%/);
    values.forEach(value => {
      expect(value).toHaveStyle({
        fontSize: '1.125rem',
        fontWeight: '600',
        color: '#111827'
      });
    });
  });

  test('layout flexbox properties work correctly', () => {
    render(<SummaryCards summary={mockSummary} />);
    
    // Check flex container properties
    const flexContainers = screen.getAllByText(/Total Emails|Passed Authentication|Failed Authentication|Pass Rate/)
      .map(text => text.closest('div')?.parentElement?.firstElementChild);
    
    flexContainers.forEach(container => {
      expect(container).toHaveStyle({
        display: 'flex',
        alignItems: 'center'
      });
    });
  });
});