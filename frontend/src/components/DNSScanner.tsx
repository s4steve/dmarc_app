import React, { useState } from 'react';
import { api } from '../utils/api';

const DNSScanner: React.FC = () => {
    const [domain, setDomain] = useState('');
    const [results, setResults] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleScan = async () => {
        try {
            const response = await api.post('/dns-scanner/scan-domain/', { domain });
            setResults(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to scan domain. Please check the domain name and try again.');
            setResults(null);
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">DNS Scanner</h1>
            <div className="flex mb-4">
                <input
                    type="text"
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    placeholder="Enter domain name"
                    className="border p-2 rounded-l w-full"
                />
                <button onClick={handleScan} className="bg-blue-500 text-white p-2 rounded-r">
                    Scan
                </button>
            </div>
            {error && <p className="text-red-500">{error}</p>}
            {results && (
                <div>
                    <h2 className="text-xl font-bold mb-2">Results for {results.domain}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="border p-4 rounded">
                            <h3 className="font-bold">DMARC</h3>
                            <p>{results.dmarc || 'Not found'}</p>
                        </div>
                        <div className="border p-4 rounded">
                            <h3 className="font-bold">SPF</h3>
                            <p>{results.spf || 'Not found'}</p>
                        </div>
                        <div className="border p-4 rounded">
                            <h3 className="font-bold">DKIM</h3>
                            <p>{results.dkim || 'Not found'}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DNSScanner;
