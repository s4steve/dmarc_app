import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDomain } from '../contexts/DomainContext';
import { spfAPI, SpfStatus, SpfSuggestion } from '../utils/api';

const errorText = (err: any) => {
  const detail = err.response?.data?.detail;
  return typeof detail === 'string' ? detail : 'Request failed. Please try again.';
};

const SpfFlattening: React.FC = () => {
  const { user } = useAuth();
  const { selectedDomain } = useDomain();
  const isAdmin = user?.role === 'admin' || user?.role === 'system_admin';
  const domain = selectedDomain?.name;

  const [status, setStatus] = useState<SpfStatus | null>(null);
  const [suggestions, setSuggestions] = useState<SpfSuggestion[]>([]);
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [manual, setManual] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Catalog includes become checkboxes; every other sender goes in the free-form box
  const showStatus = useCallback((s: SpfStatus, catalog: SpfSuggestion[]) => {
    const known = new Set(catalog.flatMap((c) => c.spf_includes));
    const senders = s.senders || [];
    setStatus(s);
    setChecked(new Set(senders.filter((x) => known.has(x))));
    setManual(senders.filter((x) => !known.has(x)).join('\n'));
  }, []);

  useEffect(() => {
    if (!domain) return;
    setError(null);
    setStatus(null);
    Promise.all([spfAPI.getStatus(domain), spfAPI.getSuggestions(domain)])
      .then(([s, catalog]) => {
        setSuggestions(catalog);
        showStatus(s, catalog);
      })
      .catch((err) => setError(errorText(err)));
  }, [domain, showStatus]);

  const run = async (action: () => Promise<SpfStatus>) => {
    setBusy(true);
    setError(null);
    try {
      showStatus(await action(), suggestions);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  };

  const toggle = (include: string) => {
    const next = new Set(checked);
    if (!next.delete(include)) next.add(include);
    setChecked(next);
  };

  const senders = Array.from(new Set([
    ...Array.from(checked),
    ...manual.split('\n').map((l) => l.trim()).filter(Boolean),
  ]));

  if (!domain) {
    return <div className="container mx-auto p-4">Select a domain to manage its SPF.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-2">Managed SPF for {domain}</h1>
      <p className="text-gray-600 mb-4">
        Pick the services that send mail as {domain}. They are flattened into IP addresses and kept
        up to date automatically, so your SPF record needs just one include and stays under the
        10-lookup limit.
      </p>
      {error && <p className="text-red-600 mb-4">{error}</p>}

      <div className="border p-4 rounded bg-white shadow-sm mb-4">
        <h2 className="font-bold mb-2">Senders</h2>
        {suggestions.map((s) => (
          <label key={s.service_name} className="flex items-center gap-2 mb-1">
            {s.spf_includes.map((inc) => (
              <input
                key={inc}
                type="checkbox"
                checked={checked.has(inc)}
                onChange={() => toggle(inc)}
                disabled={!isAdmin}
              />
            ))}
            <span>{s.service_name}</span>
            <span className="text-xs text-gray-500 font-mono">{s.spf_includes.join(', ')}</span>
            {s.emails_seen > 0 && (
              <span className="text-xs bg-green-100 text-green-800 px-2 rounded">
                seen in reports: {s.emails_seen.toLocaleString()} emails
              </span>
            )}
          </label>
        ))}
        <label className="block mt-3 mb-1 text-sm font-medium" htmlFor="spf-manual">
          Other senders: include domains, IPs or CIDRs, one per line
        </label>
        <textarea
          id="spf-manual"
          className="border p-2 rounded w-full font-mono text-sm"
          rows={4}
          value={manual}
          onChange={(e) => setManual(e.target.value)}
          disabled={!isAdmin}
          placeholder={'spf.example-sender.com\n192.0.2.0/24'}
        />
        {isAdmin && (
          <div className="flex gap-2 mt-3">
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
              disabled={busy || senders.length === 0}
              onClick={() => run(() => spfAPI.publish(domain, senders))}
            >
              {status?.configured ? 'Update' : 'Publish'}
            </button>
            {status?.configured && (
              <button
                className="border border-red-600 text-red-600 px-4 py-2 rounded disabled:opacity-50"
                disabled={busy}
                onClick={() => run(() => spfAPI.remove(domain))}
              >
                Remove
              </button>
            )}
          </div>
        )}
      </div>

      {status?.configured && (
        <div className="border p-4 rounded bg-white shadow-sm">
          <h2 className="font-bold mb-2">Status</h2>
          <ul className="text-sm space-y-1 mb-3">
            <li>Include: <span className="font-mono">{status.include}</span></li>
            <li>Flattened addresses: {status.terms?.length ?? 0}</li>
            <li>DNS lookups used by the include: {status.lookups ?? '?'} of 10</li>
            {status.updated_at && <li>Last updated: {status.updated_at}</li>}
            {status.last_error && (
              <li className="text-red-600">
                Last refresh failed (the previous addresses are still published): {status.last_error}
              </li>
            )}
            <li>
              In your SPF record:{' '}
              {status.installed === true && <span className="text-green-700">yes</span>}
              {status.installed === false && <span className="text-amber-700">not yet</span>}
              {status.installed == null && <span className="text-gray-500">couldn't check</span>}
            </li>
          </ul>
          {status.installed !== true && (
            <>
              <p className="text-sm mb-1">
                Publish this as the TXT record for {domain}, replacing your current SPF record.
                Add anything else your current record allows (such as your own mail servers) as a
                sender above first; includes for services flattened here are already covered.
              </p>
              <div className="flex gap-2">
                <code className="text-sm bg-gray-50 p-2 rounded break-all flex-1">
                  {status.suggested_record}
                </code>
                <button
                  className="border px-3 rounded"
                  onClick={() => navigator.clipboard.writeText(status.suggested_record || '')}
                >
                  Copy
                </button>
              </div>
              {status.current_record && (
                <p className="text-xs text-gray-500 mt-2 font-mono break-all">
                  Current: {status.current_record}
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SpfFlattening;
