import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import DNSScanner from '../DNSScanner';
import { api } from '../../utils/api';

jest.mock('../../utils/api');

describe('DNSScanner', () => {
    it('renders the component', () => {
        const { getByText, getByPlaceholderText } = render(<DNSScanner />);
        expect(getByText('DNS Scanner')).toBeInTheDocument();
        expect(getByPlaceholderText('Enter domain name')).toBeInTheDocument();
    });

    it('scans a domain and displays the results', async () => {
        const mockData = {
            domain: 'example.com',
            dmarc: 'v=DMARC1; p=reject',
            spf: 'v=spf1 -all',
            dkim: 'v=DKIM1; p=',
        };
        (api.post as jest.Mock).mockResolvedValue({ data: mockData });

        const { getByText, getByPlaceholderText } = render(<DNSScanner />);
        const input = getByPlaceholderText('Enter domain name');
        const scanButton = getByText('Scan');

        fireEvent.change(input, { target: { value: 'example.com' } });
        fireEvent.click(scanButton);

        await waitFor(() => {
            expect(getByText('Results for example.com')).toBeInTheDocument();
            expect(getByText('v=DMARC1; p=reject')).toBeInTheDocument();
            expect(getByText('v=spf1 -all')).toBeInTheDocument();
            expect(getByText('v=DKIM1; p=')).toBeInTheDocument();
        });
    });

    it('handles errors gracefully', async () => {
        (api.post as jest.Mock).mockRejectedValue(new Error('Failed to scan'));

        const { getByText, getByPlaceholderText } = render(<DNSScanner />);
        const input = getByPlaceholderText('Enter domain name');
        const scanButton = getByText('Scan');

        fireEvent.change(input, { target: { value: 'example.com' } });
        fireEvent.click(scanButton);

        await waitFor(() => {
            expect(getByText('Failed to scan domain. Please check the domain name and try again.')).toBeInTheDocument();
        });
    });
});
