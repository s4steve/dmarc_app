import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { adminServicesAPI, ThirdPartyService } from '../utils/api';
import { PlusIcon, PencilIcon, TrashIcon, DocumentTextIcon, CogIcon } from '@heroicons/react/24/outline';

const AdminInterface: React.FC = () => {
  const { user } = useAuth();
  const [services, setServices] = useState<ThirdPartyService[]>([]);
  const [selectedService, setSelectedService] = useState<ThirdPartyService | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isDocumentationOpen, setIsDocumentationOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadServices();
  }, []);

  // Check if user is system admin
  if (user?.role !== 'system_admin') {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        backgroundColor: '#FEF2F2',
        border: '1px solid #FECACA',
        borderRadius: '8px',
        margin: '20px',
        padding: '40px'
      }}>
        <div style={{
          width: '64px',
          height: '64px',
          backgroundColor: '#FCA5A5',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '20px'
        }}>
          <CogIcon style={{ width: '32px', height: '32px', color: '#DC2626' }} />
        </div>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#DC2626', marginBottom: '10px' }}>
          Access Denied
        </h2>
        <p style={{ fontSize: '16px', color: '#7F1D1D', textAlign: 'center' }}>
          This interface is only accessible to System Administrators.
        </p>
      </div>
    );
  }

  const loadServices = async () => {
    try {
      setLoading(true);
      const data = await adminServicesAPI.getServicesAdmin();
      setServices(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load services');
    } finally {
      setLoading(false);
    }
  };

  const handleEditService = (service: ThirdPartyService) => {
    setSelectedService(service);
    setIsEditing(true);
  };

  const handleDeleteService = async (serviceId: string) => {
    if (!window.confirm('Are you sure you want to delete this service?')) return;
    
    try {
      await adminServicesAPI.deleteService(serviceId);
      await loadServices();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete service');
    }
  };

  const handleDocumentation = (service: ThirdPartyService) => {
    setSelectedService(service);
    setIsDocumentationOpen(true);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid #E5E7EB',
          borderTop: '4px solid #3B82F6',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '2px solid #E5E7EB'
      }}>
        <div>
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: 'bold', 
            color: '#111827',
            margin: 0,
            marginBottom: '8px'
          }}>
            System Administration
          </h1>
          <p style={{ 
            fontSize: '16px', 
            color: '#6B7280',
            margin: 0
          }}>
            Manage third-party service identification rules and documentation
          </p>
        </div>
        <button
          onClick={() => {
            setSelectedService({
              service_name: '',
              ip_ranges: [],
              domain_patterns: [],
              reverse_dns_patterns: [],
              configuration_instructions: '',
              is_active: true
            });
            setIsEditing(true);
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 20px',
            backgroundColor: '#3B82F6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2563EB'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#3B82F6'}
        >
          <PlusIcon style={{ width: '20px', height: '20px' }} />
          Add New Service
        </button>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#FEF2F2',
          border: '1px solid #FECACA',
          color: '#DC2626',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '24px',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}

      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        overflow: 'hidden'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 3fr 2fr 1fr 120px',
          gap: '16px',
          padding: '16px 20px',
          backgroundColor: '#F9FAFB',
          borderBottom: '1px solid #E5E7EB',
          fontSize: '12px',
          fontWeight: '600',
          color: '#6B7280',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          <div>Service Name</div>
          <div>IP Ranges</div>
          <div>Domain Patterns</div>
          <div>Status</div>
          <div>Actions</div>
        </div>

        {services.map((service) => (
          <div
            key={service.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 3fr 2fr 1fr 120px',
              gap: '16px',
              padding: '20px',
              borderBottom: '1px solid #E5E7EB',
              alignItems: 'center'
            }}
          >
            <div>
              <div style={{ 
                fontSize: '16px', 
                fontWeight: '600', 
                color: '#111827',
                marginBottom: '4px'
              }}>
                {service.service_name}
              </div>
              {service.configuration_instructions && (
                <div style={{ 
                  fontSize: '12px', 
                  color: '#6B7280',
                  fontFamily: 'monospace',
                  backgroundColor: '#F3F4F6',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  display: 'inline-block'
                }}>
                  {service.configuration_instructions.length > 30 
                    ? service.configuration_instructions.substring(0, 30) + '...'
                    : service.configuration_instructions
                  }
                </div>
              )}
            </div>
            
            <div>
              <div style={{ fontSize: '14px', color: '#374151' }}>
                {service.ip_ranges.slice(0, 2).map((range, idx) => (
                  <div key={idx} style={{ 
                    fontFamily: 'monospace',
                    backgroundColor: '#F3F4F6',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    marginBottom: '2px',
                    fontSize: '12px'
                  }}>
                    {range}
                  </div>
                ))}
                {service.ip_ranges.length > 2 && (
                  <div style={{ fontSize: '12px', color: '#6B7280', fontStyle: 'italic' }}>
                    +{service.ip_ranges.length - 2} more
                  </div>
                )}
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '14px', color: '#374151' }}>
                {service.domain_patterns.slice(0, 2).map((pattern, idx) => (
                  <div key={idx} style={{ 
                    fontFamily: 'monospace',
                    backgroundColor: '#F3F4F6',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    marginBottom: '2px',
                    fontSize: '12px'
                  }}>
                    {pattern}
                  </div>
                ))}
                {service.domain_patterns.length > 2 && (
                  <div style={{ fontSize: '12px', color: '#6B7280', fontStyle: 'italic' }}>
                    +{service.domain_patterns.length - 2} more
                  </div>
                )}
              </div>
            </div>
            
            <div>
              <span style={{
                padding: '4px 12px',
                borderRadius: '16px',
                fontSize: '12px',
                fontWeight: '500',
                backgroundColor: service.is_active ? '#D1FAE5' : '#FEE2E2',
                color: service.is_active ? '#065F46' : '#991B1B'
              }}>
                {service.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => handleEditService(service)}
                style={{
                  padding: '6px',
                  border: 'none',
                  borderRadius: '6px',
                  backgroundColor: '#F3F4F6',
                  color: '#374151',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#E5E7EB';
                  e.currentTarget.style.color = '#111827';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#F3F4F6';
                  e.currentTarget.style.color = '#374151';
                }}
                title="Edit Service"
              >
                <PencilIcon style={{ width: '16px', height: '16px' }} />
              </button>
              
              <button
                onClick={() => handleDocumentation(service)}
                style={{
                  padding: '6px',
                  border: 'none',
                  borderRadius: '6px',
                  backgroundColor: '#FBBF24',
                  color: 'white',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F59E0B'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#FBBF24'}
                title="Manage Documentation"
              >
                <DocumentTextIcon style={{ width: '16px', height: '16px' }} />
              </button>
              
              <button
                onClick={() => service.id && handleDeleteService(service.id)}
                style={{
                  padding: '6px',
                  border: 'none',
                  borderRadius: '6px',
                  backgroundColor: '#EF4444',
                  color: 'white',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#DC2626'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#EF4444'}
                title="Delete Service"
              >
                <TrashIcon style={{ width: '16px', height: '16px' }} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Service Edit Modal */}
      {isEditing && selectedService && (
        <ServiceEditModal
          service={selectedService}
          onSave={async (updatedService) => {
            try {
              if (updatedService.id) {
                await adminServicesAPI.updateService(updatedService.id, updatedService);
              } else {
                await adminServicesAPI.addService(updatedService);
              }
              await loadServices();
              setIsEditing(false);
              setSelectedService(null);
            } catch (err: any) {
              setError(err.response?.data?.detail || 'Failed to save service');
            }
          }}
          onCancel={() => {
            setIsEditing(false);
            setSelectedService(null);
          }}
        />
      )}

      {/* Documentation Modal */}
      {isDocumentationOpen && selectedService && (
        <DocumentationModal
          service={selectedService}
          onSave={async (docData) => {
            try {
              if (selectedService.id) {
                await adminServicesAPI.updateDocumentation(selectedService.id, docData);
                await loadServices();
              }
              setIsDocumentationOpen(false);
              setSelectedService(null);
            } catch (err: any) {
              setError(err.response?.data?.detail || 'Failed to save documentation');
            }
          }}
          onCancel={() => {
            setIsDocumentationOpen(false);
            setSelectedService(null);
          }}
        />
      )}
    </div>
  );
};

// Service Edit Modal Component
interface ServiceEditModalProps {
  service: ThirdPartyService;
  onSave: (service: ThirdPartyService) => void;
  onCancel: () => void;
}

const ServiceEditModal: React.FC<ServiceEditModalProps> = ({ service, onSave, onCancel }) => {
  const [formData, setFormData] = useState<ThirdPartyService>({ ...service });

  const handleArrayChange = (field: keyof ThirdPartyService, index: number, value: string) => {
    const array = [...(formData[field] as string[])];
    array[index] = value;
    setFormData({ ...formData, [field]: array });
  };

  const addArrayItem = (field: keyof ThirdPartyService) => {
    const array = [...(formData[field] as string[])];
    array.push('');
    setFormData({ ...formData, [field]: array });
  };

  const removeArrayItem = (field: keyof ThirdPartyService, index: number) => {
    const array = [...(formData[field] as string[])];
    array.splice(index, 1);
    setFormData({ ...formData, [field]: array });
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        width: '90%',
        maxWidth: '600px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
          {service.id ? 'Edit Service' : 'Add New Service'}
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
              Service Name
            </label>
            <input
              type="text"
              value={formData.service_name}
              onChange={(e) => setFormData({ ...formData, service_name: e.target.value })}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #D1D5DB',
                borderRadius: '6px',
                fontSize: '14px'
              }}
            />
          </div>

          <ArrayFieldEditor
            label="IP Ranges"
            values={formData.ip_ranges}
            onChange={(values) => setFormData({ ...formData, ip_ranges: values })}
            placeholder="e.g., 192.168.1.0/24"
          />

          <ArrayFieldEditor
            label="Domain Patterns"
            values={formData.domain_patterns}
            onChange={(values) => setFormData({ ...formData, domain_patterns: values })}
            placeholder="e.g., *.example.com"
          />

          <ArrayFieldEditor
            label="Reverse DNS Patterns"
            values={formData.reverse_dns_patterns}
            onChange={(values) => setFormData({ ...formData, reverse_dns_patterns: values })}
            placeholder="e.g., *.mail.example.com"
          />

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
              Configuration Instructions
            </label>
            <textarea
              value={formData.configuration_instructions || ''}
              onChange={(e) => setFormData({ ...formData, configuration_instructions: e.target.value })}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #D1D5DB',
                borderRadius: '6px',
                fontSize: '14px',
                minHeight: '80px',
                fontFamily: 'monospace'
              }}
              placeholder="e.g., Add 'include:spf.example.com' to your SPF record"
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              style={{ width: '16px', height: '16px' }}
            />
            <label style={{ fontSize: '14px', fontWeight: '500' }}>
              Active
            </label>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '24px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              border: '1px solid #D1D5DB',
              borderRadius: '6px',
              backgroundColor: 'white',
              color: '#374151',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(formData)}
            style={{
              padding: '10px 20px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: '#3B82F6',
              color: 'white',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

// Array Field Editor Component
interface ArrayFieldEditorProps {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
}

const ArrayFieldEditor: React.FC<ArrayFieldEditorProps> = ({ label, values, onChange, placeholder }) => {
  const handleChange = (index: number, value: string) => {
    const newValues = [...values];
    newValues[index] = value;
    onChange(newValues);
  };

  const addItem = () => {
    onChange([...values, '']);
  };

  const removeItem = (index: number) => {
    const newValues = values.filter((_, i) => i !== index);
    onChange(newValues);
  };

  return (
    <div>
      <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
        {label}
      </label>
      {values.map((value, index) => (
        <div key={index} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <input
            type="text"
            value={value}
            onChange={(e) => handleChange(index, e.target.value)}
            placeholder={placeholder}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: '1px solid #D1D5DB',
              borderRadius: '6px',
              fontSize: '14px',
              fontFamily: 'monospace'
            }}
          />
          <button
            onClick={() => removeItem(index)}
            style={{
              padding: '8px 12px',
              border: '1px solid #EF4444',
              borderRadius: '6px',
              backgroundColor: 'white',
              color: '#EF4444',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Remove
          </button>
        </div>
      ))}
      <button
        onClick={addItem}
        style={{
          padding: '8px 16px',
          border: '1px solid #3B82F6',
          borderRadius: '6px',
          backgroundColor: 'white',
          color: '#3B82F6',
          fontSize: '12px',
          cursor: 'pointer'
        }}
      >
        Add {label.slice(0, -1)}
      </button>
    </div>
  );
};

// Documentation Modal Component
interface DocumentationModalProps {
  service: ThirdPartyService;
  onSave: (docData: { documentation: string; setup_guide?: string; troubleshooting?: string }) => void;
  onCancel: () => void;
}

const DocumentationModal: React.FC<DocumentationModalProps> = ({ service, onSave, onCancel }) => {
  const [documentation, setDocumentation] = useState(service.documentation || '');
  const [setupGuide, setSetupGuide] = useState(service.setup_guide || '');
  const [troubleshooting, setTroubleshooting] = useState(service.troubleshooting || '');

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        width: '90%',
        maxWidth: '700px',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
          Documentation for {service.service_name}
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
              General Documentation
            </label>
            <textarea
              value={documentation}
              onChange={(e) => setDocumentation(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '14px',
                minHeight: '120px',
                fontFamily: 'monospace'
              }}
              placeholder="Enter general documentation about this service..."
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
              Setup Guide
            </label>
            <textarea
              value={setupGuide}
              onChange={(e) => setSetupGuide(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '14px',
                minHeight: '120px',
                fontFamily: 'monospace'
              }}
              placeholder="Enter step-by-step setup instructions..."
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
              Troubleshooting
            </label>
            <textarea
              value={troubleshooting}
              onChange={(e) => setTroubleshooting(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D1D5DB',
                borderRadius: '8px',
                fontSize: '14px',
                minHeight: '120px',
                fontFamily: 'monospace'
              }}
              placeholder="Enter common issues and solutions..."
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '24px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '12px 24px',
              border: '1px solid #D1D5DB',
              borderRadius: '8px',
              backgroundColor: 'white',
              color: '#374151',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => onSave({ documentation, setup_guide: setupGuide, troubleshooting })}
            style={{
              padding: '12px 24px',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: '#3B82F6',
              color: 'white',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Save Documentation
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminInterface;