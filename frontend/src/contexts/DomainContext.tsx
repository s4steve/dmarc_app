import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { domainAPI, Domain } from '../utils/api';
import { useAuth } from './AuthContext';


interface DomainContextType {
  domains: Domain[];
  selectedDomain: Domain | null;
  setSelectedDomain: (domain: Domain | null) => void;
  addDomain: (domainName: string) => Promise<void>;
  loadDomains: () => Promise<void>;
  isLoading: boolean;
  error: string;
}

const DomainContext = createContext<DomainContextType | undefined>(undefined);

export const useDomain = () => {
  const context = useContext(DomainContext);
  if (context === undefined) {
    throw new Error('useDomain must be used within a DomainProvider');
  }
  return context;
};

interface DomainProviderProps {
  children: ReactNode;
}

export const DomainProvider: React.FC<DomainProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const loadDomains = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const domainsData = await domainAPI.getDomains();

      setDomains(domainsData);
      
      // Set the first domain as selected if none is selected
      if (!selectedDomain && domainsData.length > 0) {
        setSelectedDomain(domainsData[0]);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load domains');
    } finally {
      setIsLoading(false);
    }
  };

  const addDomain = async (domainName: string) => {
    try {
      setIsLoading(true);
      setError('');
      
      const newDomain = await domainAPI.addDomain(domainName);

      setDomains(prev => [...prev, newDomain]);
      
      // Select the newly added domain
      setSelectedDomain(newDomain);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add domain');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // Domains need a logged-in user: loading them on the login page got a 401, whose
  // redirect to /login reloaded the page and requested them again, forever.
  useEffect(() => {
    if (user) {
      loadDomains();
    } else {
      setDomains([]);
      setSelectedDomain(null);
    }
  }, [user]);

  return (
    <DomainContext.Provider
      value={{
        domains,
        selectedDomain,
        setSelectedDomain,
        addDomain,
        loadDomains,
        isLoading,
        error
      }}
    >
      {children}
    </DomainContext.Provider>
  );
};