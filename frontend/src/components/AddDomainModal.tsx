import React, { useState } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { useDomain } from '../contexts/DomainContext';

interface AddDomainModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AddDomainModal: React.FC<AddDomainModalProps> = ({ isOpen, onClose }) => {
  const [domainName, setDomainName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const { addDomain } = useDomain();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!domainName.trim()) {
      setError('Please enter a domain name');
      return;
    }

    // Basic domain validation
    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
    if (!domainRegex.test(domainName.trim())) {
      setError('Please enter a valid domain name (e.g., example.com)');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');
      await addDomain(domainName.trim().toLowerCase());
      setDomainName('');
      onClose();
    } catch (err) {
      setError('Failed to add domain. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setDomainName('');
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        width: '100%',
        maxWidth: '28rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#111827' }}>
            Add Domain for DMARC Monitoring
          </h3>
          <button
            onClick={handleClose}
            style={{
              padding: '0.25rem',
              color: '#6B7280',
              backgroundColor: 'transparent',
              border: 'none',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              transition: 'color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#374151'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#6B7280'}
          >
            <XMarkIcon style={{ height: '1.25rem', width: '1.25rem' }} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label 
              htmlFor="domain" 
              style={{ 
                display: 'block', 
                fontSize: '0.875rem', 
                fontWeight: '500', 
                color: '#374151', 
                marginBottom: '0.5rem' 
              }}
            >
              Domain Name
            </label>
            <input
              type="text"
              id="domain"
              value={domainName}
              onChange={(e) => setDomainName(e.target.value)}
              placeholder="example.com"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #D1D5DB',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                outline: 'none',
                transition: 'border-color 0.2s, box-shadow 0.2s'
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = '#2563EB';
                e.currentTarget.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.1)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = '#D1D5DB';
                e.currentTarget.style.boxShadow = 'none';
              }}
            />
            <p style={{ fontSize: '0.75rem', color: '#6B7280', marginTop: '0.25rem' }}>
              Enter the domain you want to monitor for DMARC reports
            </p>
          </div>

          {error && (
            <div style={{
              backgroundColor: '#FEF2F2',
              border: '1px solid #FECACA',
              color: '#DC2626',
              padding: '0.75rem',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              marginBottom: '1rem'
            }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={handleClose}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#374151',
                backgroundColor: 'white',
                border: '1px solid #D1D5DB',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F9FAFB'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: 'white',
                backgroundColor: isSubmitting ? '#93C5FD' : '#2563EB',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!isSubmitting) e.currentTarget.style.backgroundColor = '#1D4ED8';
              }}
              onMouseLeave={(e) => {
                if (!isSubmitting) e.currentTarget.style.backgroundColor = '#2563EB';
              }}
            >
              {isSubmitting ? (
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
                  Adding...
                </>
              ) : (
                <>
                  <PlusIcon style={{ height: '1rem', width: '1rem', marginRight: '0.5rem' }} />
                  Add Domain
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddDomainModal;