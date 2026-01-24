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
                    <div className="grid grid-cols-1 gap-4">
                        <div className="border p-4 rounded bg-white shadow-sm">
                            <h3 className="font-bold text-blue-600 mb-2">DMARC Record</h3>
                            <p className="text-sm font-mono bg-gray-50 p-3 rounded break-all whitespace-pre-wrap overflow-hidden">
                                {results.dmarc || 'Not found'}
                            </p>
                        </div>
                        <div className="border p-4 rounded bg-white shadow-sm">
                            <h3 className="font-bold text-green-600 mb-2">SPF Record</h3>
                            <p className="text-sm font-mono bg-gray-50 p-3 rounded break-all whitespace-pre-wrap overflow-hidden">
                                {results.spf || 'Not found'}
                            </p>
                        </div>
                        <div className="border p-4 rounded bg-white shadow-sm">
                            <h3 className="font-bold text-purple-600 mb-2">DKIM Record</h3>
                            <p className="text-sm font-mono bg-gray-50 p-3 rounded break-all whitespace-pre-wrap overflow-hidden">
                                {results.dkim || 'Not found'}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DNSScanner;
