import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { DomainProvider } from './contexts/DomainContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F9FAFB' }}>
        <div style={{ 
          animation: 'spin 1s linear infinite', 
          borderRadius: '50%', 
          height: '8rem', 
          width: '8rem', 
          borderBottom: '2px solid #2563EB' 
        }}></div>
      </div>
    );
  }

  return isAuthenticated ? (
    <DomainProvider>
      <Dashboard />
    </DomainProvider>
  ) : <Login />;
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
