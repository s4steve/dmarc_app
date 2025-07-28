import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useDomain } from '../contexts/DomainContext';
import { Menu, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { 
  UserCircleIcon, 
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon,
  PlusIcon,
  ChevronDownIcon 
} from '@heroicons/react/24/outline';
import AddDomainModal from './AddDomainModal';

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { domains, selectedDomain, setSelectedDomain } = useDomain();
  const [isAddDomainModalOpen, setIsAddDomainModalOpen] = useState(false);

  return (
    <header style={{ backgroundColor: 'white', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '0 1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', height: '4rem' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
              <ShieldCheckIcon style={{ height: '2rem', width: '2rem', color: '#2563EB' }} />
              <span style={{ marginLeft: '0.5rem', fontSize: '1.25rem', fontWeight: 'bold', color: '#111827' }}>
                DMARC Analytics
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Domain Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Menu as="div" style={{ position: 'relative' }}>
                <Menu.Button style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  backgroundColor: '#F3F4F6',
                  border: '1px solid #D1D5DB',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#E5E7EB';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#F3F4F6';
                }}
                >
                  <span style={{ marginRight: '0.5rem' }}>
                    {selectedDomain ? selectedDomain.name : 'Select Domain'}
                  </span>
                  <ChevronDownIcon style={{ height: '1rem', width: '1rem' }} />
                </Menu.Button>
                
                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items style={{
                    position: 'absolute',
                    left: 0,
                    marginTop: '0.5rem',
                    width: '12rem',
                    borderRadius: '0.375rem',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                    backgroundColor: 'white',
                    border: '1px solid rgba(0, 0, 0, 0.05)',
                    outline: 'none',
                    zIndex: 10
                  }}>
                    <div style={{ padding: '0.25rem 0' }}>
                      {domains.length > 0 ? (
                        domains.map((domain) => (
                          <Menu.Item key={domain.id}>
                            {({ active }) => (
                              <button
                                onClick={() => setSelectedDomain(domain)}
                                style={{
                                  backgroundColor: active ? '#F3F4F6' : 'transparent',
                                  display: 'flex',
                                  width: '100%',
                                  alignItems: 'center',
                                  padding: '0.5rem 1rem',
                                  fontSize: '0.875rem',
                                  color: selectedDomain?.id === domain.id ? '#2563EB' : '#374151',
                                  fontWeight: selectedDomain?.id === domain.id ? '600' : '400',
                                  border: 'none',
                                  cursor: 'pointer',
                                  textAlign: 'left'
                                }}
                              >
                                {domain.name}
                              </button>
                            )}
                          </Menu.Item>
                        ))
                      ) : (
                        <div style={{
                          padding: '0.5rem 1rem',
                          fontSize: '0.875rem',
                          color: '#6B7280',
                          textAlign: 'center'
                        }}>
                          No domains added
                        </div>
                      )}
                    </div>
                  </Menu.Items>
                </Transition>
              </Menu>
              
              <button
                onClick={() => setIsAddDomainModalOpen(true)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0.5rem',
                  backgroundColor: '#2563EB',
                  border: 'none',
                  borderRadius: '0.375rem',
                  color: 'white',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1D4ED8'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2563EB'}
                title="Add Domain"
              >
                <PlusIcon style={{ height: '1rem', width: '1rem' }} />
              </button>
            </div>
            
            <div style={{ marginLeft: '0.75rem', position: 'relative' }}>
              <Menu as="div" className="relative inline-block text-left">
                <div>
                  <Menu.Button style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    fontSize: '0.875rem', 
                    borderRadius: '9999px', 
                    backgroundColor: 'transparent',
                    border: 'none',
                    cursor: 'pointer'
                  }}>
                    <UserCircleIcon style={{ height: '2rem', width: '2rem', color: '#9CA3AF' }} />
                    <span style={{ marginLeft: '0.5rem', color: '#374151', fontWeight: '500' }}>
                      {user?.full_name || user?.email}
                    </span>
                  </Menu.Button>
                </div>
                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items style={{
                    position: 'absolute',
                    right: 0,
                    marginTop: '0.5rem',
                    width: '14rem',
                    borderRadius: '0.375rem',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                    backgroundColor: 'white',
                    border: '1px solid rgba(0, 0, 0, 0.05)',
                    outline: 'none'
                  }}>
                    <div style={{ padding: '0.25rem 0' }}>
                      <div style={{ 
                        padding: '0.5rem 1rem', 
                        fontSize: '0.875rem', 
                        color: '#6B7280', 
                        borderBottom: '1px solid #E5E7EB' 
                      }}>
                        <div style={{ fontWeight: '500' }}>{user?.full_name || user?.email}</div>
                        <div style={{ fontSize: '0.75rem' }}>{user?.role}</div>
                      </div>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={logout}
                            style={{
                              backgroundColor: active ? '#F3F4F6' : 'transparent',
                              display: 'flex',
                              width: '100%',
                              alignItems: 'center',
                              padding: '0.5rem 1rem',
                              fontSize: '0.875rem',
                              color: '#374151',
                              border: 'none',
                              cursor: 'pointer'
                            }}
                          >
                            <ArrowRightOnRectangleIcon style={{ marginRight: '0.75rem', height: '1rem', width: '1rem' }} />
                            Sign out
                          </button>
                        )}
                      </Menu.Item>
                    </div>
                  </Menu.Items>
                </Transition>
              </Menu>
            </div>
          </div>
        </div>
      </div>
      
      <AddDomainModal
        isOpen={isAddDomainModalOpen}
        onClose={() => setIsAddDomainModalOpen(false)}
      />
    </header>
  );
};

export default Header;