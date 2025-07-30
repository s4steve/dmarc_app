import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  customer_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Domain {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface DMARCReportSummary {
  total_emails: number;
  passed_emails: number;
  failed_emails: number;
  pass_rate: number;
  date_range: {
    start: string;
    end: string;
  };
  top_services: Array<{
    service: string;
    email_count: number;
  }>;
}

export interface TimeSeriesData {
  date: string;
  total_emails: number;
  passed_emails: number;
  failed_emails: number;
  pass_rate: number;
}

export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
};

export const dmarcAPI = {
  getSummary: async (days: number = 7, domain?: string): Promise<DMARCReportSummary> => {
    const params = new URLSearchParams({ days: days.toString() });
    if (domain) {
      params.append('domain', domain);
    }
    const response = await api.get(`/dmarc/summary?${params}`);
    return response.data;
  },
  
  getTimeSeriesData: async (days: number = 30, domain?: string): Promise<TimeSeriesData[]> => {
    const params = new URLSearchParams({ days: days.toString() });
    if (domain) {
      params.append('domain', domain);
    }
    const response = await api.get(`/dmarc/time-series?${params}`);
    return response.data;
  },
  
  getReports: async (limit: number = 100, domain?: string) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (domain) {
      params.append('domain', domain);
    }
    const response = await api.get(`/dmarc/reports?${params}`);
    return response.data;
  },
  
  uploadReport: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/dmarc/upload-report', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const userAPI = {
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/users/me');
    return response.data;
  },
  
  getUsers: async (): Promise<User[]> => {
    const response = await api.get('/users/');
    return response.data;
  },
};

export const domainAPI = {
  getDomains: async (): Promise<Domain[]> => {
    const response = await api.get('/domains/');
    return response.data;
  },
  
  addDomain: async (name: string): Promise<Domain> => {
    const response = await api.post('/domains/', { name });
    return response.data;
  },
  
  deleteDomain: async (id: string): Promise<void> => {
    await api.delete(`/domains/${id}`);
  },
};

export interface ThirdPartyService {
  id?: string;
  service_name: string;
  ip_ranges: string[];
  domain_patterns: string[];
  reverse_dns_patterns: string[];
  configuration_instructions?: string;
  documentation?: string;
  setup_guide?: string;
  troubleshooting?: string;
  is_active: boolean;
}

export const servicesAPI = {
  getServices: async () => {
    const response = await api.get('/services/');
    return response.data;
  },
  
  initializeServices: async () => {
    const response = await api.post('/services/initialize');
    return response.data;
  },
};

export const adminServicesAPI = {
  getServicesAdmin: async (): Promise<ThirdPartyService[]> => {
    const response = await api.get('/services/admin');
    return response.data;
  },
  
  getServiceDetails: async (serviceId: string): Promise<ThirdPartyService> => {
    const response = await api.get(`/services/admin/${serviceId}`);
    return response.data;
  },
  
  updateService: async (serviceId: string, serviceData: Partial<ThirdPartyService>) => {
    const response = await api.put(`/services/admin/${serviceId}`, serviceData);
    return response.data;
  },
  
  deleteService: async (serviceId: string) => {
    const response = await api.delete(`/services/admin/${serviceId}`);
    return response.data;
  },
  
  addService: async (service: ThirdPartyService) => {
    const response = await api.post('/services/', service);
    return response.data;
  },
  
  updateDocumentation: async (serviceId: string, docData: {
    documentation: string;
    setup_guide?: string;
    troubleshooting?: string;
  }) => {
    const response = await api.post(`/services/admin/${serviceId}/documentation`, {
      service_id: serviceId,
      ...docData
    });
    return response.data;
  },
  
  recreateIndex: async () => {
    const response = await api.post('/services/admin/recreate-index');
    return response.data;
  },
};

export default api;