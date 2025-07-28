import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LockClosedIcon } from '@heroicons/react/24/solid';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#F9FAFB',
      padding: '3rem 1rem'
    }}>
      <div style={{
        maxWidth: '28rem',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            margin: '0 auto',
            height: '3rem',
            width: '3rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '50%',
            backgroundColor: '#DBEAFE'
          }}>
            <LockClosedIcon style={{ height: '1.5rem', width: '1.5rem', color: '#2563EB' }} />
          </div>
          <h2 style={{
            marginTop: '1.5rem',
            textAlign: 'center',
            fontSize: '1.875rem',
            fontWeight: '800',
            color: '#111827'
          }}>
            Sign in to DMARC Analytics
          </h2>
          <p style={{
            marginTop: '0.5rem',
            textAlign: 'center',
            fontSize: '0.875rem',
            color: '#6B7280'
          }}>
            Monitor and analyze your email authentication
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{
            borderRadius: '0.375rem',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
            overflow: 'hidden'
          }}>
            <div>
              <label htmlFor="email-address" style={{ display: 'none' }}>
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                style={{
                  appearance: 'none',
                  position: 'relative',
                  display: 'block',
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #D1D5DB',
                  borderBottom: 'none',
                  borderTopLeftRadius: '0.375rem',
                  borderTopRightRadius: '0.375rem',
                  fontSize: '0.875rem',
                  color: '#111827',
                  backgroundColor: 'white',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#2563EB';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.1)';
                  e.currentTarget.style.zIndex = '10';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#D1D5DB';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.zIndex = 'auto';
                }}
              />
            </div>
            <div>
              <label htmlFor="password" style={{ display: 'none' }}>
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                style={{
                  appearance: 'none',
                  position: 'relative',
                  display: 'block',
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #D1D5DB',
                  borderBottomLeftRadius: '0.375rem',
                  borderBottomRightRadius: '0.375rem',
                  fontSize: '0.875rem',
                  color: '#111827',
                  backgroundColor: 'white',
                  outline: 'none',
                  transition: 'all 0.2s'
                }}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = '#2563EB';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.1)';
                  e.currentTarget.style.zIndex = '10';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = '#D1D5DB';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.zIndex = 'auto';
                }}
              />
            </div>
          </div>

          {error && (
            <div style={{
              backgroundColor: '#FEF2F2',
              border: '1px solid #FECACA',
              color: '#DC2626',
              padding: '0.75rem 1rem',
              borderRadius: '0.375rem',
              fontSize: '0.875rem'
            }}>
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                position: 'relative',
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '0.75rem 1rem',
                border: 'none',
                fontSize: '0.875rem',
                fontWeight: '500',
                borderRadius: '0.375rem',
                color: 'white',
                backgroundColor: isLoading ? '#93C5FD' : '#2563EB',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s',
                outline: 'none'
              }}
              onMouseEnter={(e) => {
                if (!isLoading && e.currentTarget.style.backgroundColor === 'rgb(37, 99, 235)') {
                  e.currentTarget.style.backgroundColor = '#1D4ED8';
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = '#2563EB';
                }
              }}
              onFocus={(e) => {
                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.5)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              {isLoading ? (
                <>
                  <div style={{
                    animation: 'spin 1s linear infinite',
                    borderRadius: '50%',
                    height: '1rem',
                    width: '1rem',
                    borderTop: '2px solid white',
                    borderRight: '2px solid transparent',
                    marginRight: '0.5rem'
                  }}></div>
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          <div style={{
            textAlign: 'center',
            fontSize: '0.875rem',
            color: '#6B7280',
            marginTop: '1rem'
          }}>
            <p>Default credentials for testing:</p>
            <p style={{ fontFamily: 'monospace', marginTop: '0.25rem' }}>
              <strong>Email:</strong> admin@example.com<br />
              <strong>Password:</strong> admin123
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;