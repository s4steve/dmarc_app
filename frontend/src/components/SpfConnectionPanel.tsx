import React, { useEffect, useState } from 'react';
import { CheckCircleIcon, ExclamationTriangleIcon, XCircleIcon } from '@heroicons/react/24/solid';
import { spfAdminAPI, SpfConnectionCheck, SpfConnectionStatus } from '../utils/api';

const errorText = (err: any) => {
  const detail = err.response?.data?.detail;
  return typeof detail === 'string' ? detail : 'Request failed. Please try again.';
};

const checkIcon = {
  pass: <CheckCircleIcon className="h-5 w-5 text-green-600 flex-none" aria-label="passed" />,
  warn: <ExclamationTriangleIcon className="h-5 w-5 text-amber-500 flex-none" aria-label="warning" />,
  fail: <XCircleIcon className="h-5 w-5 text-red-600 flex-none" aria-label="failed" />,
};

// Read-only: the settings live in .env, and the token is never sent to the browser
const SpfConnectionPanel: React.FC = () => {
  const [status, setStatus] = useState<SpfConnectionStatus | null>(null);
  const [checks, setChecks] = useState<SpfConnectionCheck[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    spfAdminAPI.getStatus().then(setStatus).catch((err) => setError(errorText(err)));
  }, []);

  const runTest = async () => {
    setTesting(true);
    setError(null);
    setChecks(null);
    try {
      setChecks((await spfAdminAPI.testConnection()).checks);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setTesting(false);
    }
  };

  const state = !status
    ? null
    : !status.configured
      ? { label: 'Not configured', className: 'bg-gray-100 text-gray-700' }
      : status.transport_error
        ? { label: 'Misconfigured', className: 'bg-red-100 text-red-800' }
        : { label: 'Configured', className: 'bg-green-100 text-green-800' };

  return (
    <section className="border rounded-lg bg-white shadow-sm p-5 mb-6" aria-labelledby="spf-connection-title">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h2 id="spf-connection-title" className="text-lg font-bold flex items-center gap-2">
            Managed SPF connection
            {state && <span className={`text-xs font-medium px-2 py-0.5 rounded ${state.className}`}>{state.label}</span>}
          </h2>
          <p className="text-sm text-gray-600">
            The DNS server control plane that publishes customers' flattened SPF records. Set in the API's
            <code className="mx-1">.env</code>and applied when the API restarts.
          </p>
        </div>
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
          onClick={runTest}
          disabled={testing || !status}
        >
          {testing ? 'Testing…' : 'Test connection'}
        </button>
      </div>

      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      {status && (
        <dl className="grid grid-cols-1 sm:grid-cols-[max-content_1fr] gap-x-6 gap-y-1 text-sm">
          <dt className="text-gray-500">Control plane URL</dt>
          <dd className="font-mono break-all">{status.url || <span className="text-gray-400">not set</span>}</dd>
          <dt className="text-gray-500">SPF zone</dt>
          <dd className="font-mono break-all">{status.zone || <span className="text-gray-400">not set</span>}</dd>
          <dt className="text-gray-500">Token</dt>
          <dd>{status.token_set ? 'set (hidden)' : <span className="text-gray-400">not set</span>}</dd>
          <dt className="text-gray-500">Plain http allowed</dt>
          <dd>{status.allow_http ? 'yes (development only)' : 'no'}</dd>
          {status.transport_error && (
            <>
              <dt className="text-gray-500">Problem</dt>
              <dd className="text-red-700">{status.transport_error}</dd>
            </>
          )}
        </dl>
      )}

      {checks && (
        <ul className="mt-4 border-t pt-4 space-y-2" aria-live="polite">
          {checks.map((c) => (
            <li key={c.name} className="flex gap-3 text-sm">
              {checkIcon[c.status]}
              <span>
                <span className="font-medium">{c.name}</span>
                <span className="text-gray-600"> · {c.detail}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default SpfConnectionPanel;
