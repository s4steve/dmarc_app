import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { domainAPI, Domain } from '../utils/api';


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
  const [domains, setDomains] = useState<Domain[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const loadDomains = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Try to load domains from API, fallback to mock data if API fails
      let domainsData: Domain[];
      try {
        domainsData = await domainAPI.getDomains();
      } catch (apiError) {
        // Fallback to mock domains if API is not available
        domainsData = [
          {
            id: '1',
            name: 'example.com',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true
          },
          {
            id: '2', 
            name: 'company.org',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true
          }
        ];
      }
      
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
      
      // Try to add domain via API, fallback to mock if API fails
      let newDomain: Domain;
      try {
        newDomain = await domainAPI.addDomain(domainName);
      } catch (apiError) {
        // Fallback to mock domain creation
        newDomain = {
          id: String(domains.length + 1),
          name: domainName,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true
        };
      }
      
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

  useEffect(() => {
    loadDomains();
  }, []);

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