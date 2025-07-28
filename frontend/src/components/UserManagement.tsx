import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI, User } from '../utils/api';
import { 
  PlusIcon, 
  TrashIcon, 
  PencilIcon,
  UserIcon 
} from '@heroicons/react/24/outline';

const UserManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      setError('');
      const usersData = await userAPI.getUsers();
      setUsers(usersData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleBadgeStyle = (role: string) => {
    switch (role) {
      case 'admin':
        return { backgroundColor: '#DBEAFE', color: '#1E40AF' };
      case 'system_admin':
        return { backgroundColor: '#E9D5FF', color: '#7C3AED' };
      case 'read_only':
        return { backgroundColor: '#F3F4F6', color: '#1F2937' };
      default:
        return { backgroundColor: '#F3F4F6', color: '#1F2937' };
    }
  };

  if (!currentUser || !['admin', 'system_admin'].includes(currentUser.role)) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ 
          backgroundColor: '#FEF2F2', 
          border: '1px solid #FECACA', 
          color: '#DC2626', 
          padding: '1rem', 
          borderRadius: '0.375rem' 
        }}>
          You don't have permission to access user management.
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '16rem' }}>
          <div style={{ 
            animation: 'spin 1s linear infinite', 
            borderRadius: '50%', 
            height: '8rem', 
            width: '8rem', 
            borderBottom: '2px solid #2563EB' 
          }}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
        <div style={{ 
          backgroundColor: '#FEF2F2', 
          border: '1px solid #FECACA', 
          color: '#DC2626', 
          padding: '1rem', 
          borderRadius: '0.375rem' 
        }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '1.5rem' }}>
      <div style={{ padding: '1.5rem 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: '#111827' }}>User Management</h1>
            <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
              Manage user accounts and permissions
            </p>
          </div>
          <button style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '0.5rem 1rem',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: '500',
            borderRadius: '0.375rem',
            color: 'white',
            backgroundColor: '#2563EB',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1D4ED8'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2563EB'}
          >
            <PlusIcon style={{ height: '1rem', width: '1rem', marginRight: '0.5rem' }} />
            Add User
          </button>
        </div>

        <div style={{ 
          backgroundColor: 'white', 
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', 
          borderRadius: '0.375rem',
          overflow: 'hidden'
        }}>
          <ul style={{ display: 'flex', flexDirection: 'column' }}>
            {users.map((user, index) => (
              <li key={user.id} style={{ 
                borderBottom: index < users.length - 1 ? '1px solid #E5E7EB' : 'none' 
              }}>
                <div style={{ padding: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <div style={{ flexShrink: 0 }}>
                        <UserIcon style={{ height: '2.5rem', width: '2.5rem', color: '#9CA3AF' }} />
                      </div>
                      <div style={{ marginLeft: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <p style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>
                            {user.full_name || user.email}
                          </p>
                          {user.id === currentUser.id && (
                            <span style={{
                              marginLeft: '0.5rem',
                              display: 'inline-flex',
                              alignItems: 'center',
                              padding: '0.125rem 0.625rem',
                              borderRadius: '9999px',
                              fontSize: '0.75rem',
                              fontWeight: '500',
                              backgroundColor: '#DCFCE7',
                              color: '#166534'
                            }}>
                              You
                            </span>
                          )}
                        </div>
                        <p style={{ fontSize: '0.875rem', color: '#6B7280' }}>{user.email}</p>
                        <div style={{ display: 'flex', alignItems: 'center', marginTop: '0.25rem' }}>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '0.125rem 0.625rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '500',
                            ...getRoleBadgeStyle(user.role)
                          }}>
                            {user.role.replace('_', ' ').toUpperCase()}
                          </span>
                          <span style={{
                            marginLeft: '0.5rem',
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '0.125rem 0.625rem',
                            borderRadius: '9999px',
                            fontSize: '0.75rem',
                            fontWeight: '500',
                            backgroundColor: user.is_active ? '#DCFCE7' : '#FEE2E2',
                            color: user.is_active ? '#166534' : '#991B1B'
                          }}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <button style={{
                        padding: '0.5rem',
                        color: '#9CA3AF',
                        backgroundColor: 'transparent',
                        border: 'none',
                        borderRadius: '0.25rem',
                        cursor: 'pointer',
                        transition: 'color 0.2s'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.color = '#4B5563'}
                      onMouseLeave={(e) => e.currentTarget.style.color = '#9CA3AF'}
                      >
                        <PencilIcon style={{ height: '1rem', width: '1rem' }} />
                      </button>
                      {user.id !== currentUser.id && (
                        <button style={{
                          padding: '0.5rem',
                          color: '#F87171',
                          backgroundColor: 'transparent',
                          border: 'none',
                          borderRadius: '0.25rem',
                          cursor: 'pointer',
                          transition: 'color 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.color = '#DC2626'}
                        onMouseLeave={(e) => e.currentTarget.style.color = '#F87171'}
                        >
                          <TrashIcon style={{ height: '1rem', width: '1rem' }} />
                        </button>
                      )}
                    </div>
                  </div>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6B7280' }}>
                    <p>Created: {new Date(user.created_at).toLocaleDateString()}</p>
                    <p>Last updated: {new Date(user.updated_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {users.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <UserIcon style={{ margin: '0 auto', height: '3rem', width: '3rem', color: '#9CA3AF' }} />
            <h3 style={{ marginTop: '0.5rem', fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>No users</h3>
            <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#6B7280' }}>
              Get started by adding a new user to your organization.
            </p>
            <div style={{ marginTop: '1.5rem' }}>
              <button style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '0.5rem 1rem',
                border: 'none',
                boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
                fontSize: '0.875rem',
                fontWeight: '500',
                borderRadius: '0.375rem',
                color: 'white',
                backgroundColor: '#2563EB',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1D4ED8'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2563EB'}
              >
                <PlusIcon style={{ height: '1rem', width: '1rem', marginRight: '0.5rem' }} />
                Add User
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement;