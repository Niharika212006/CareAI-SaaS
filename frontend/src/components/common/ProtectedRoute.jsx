import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Activity } from 'lucide-react';
import useAuth from '../../hooks/useAuth';
import { USER_ROLES } from '../../utils/constants';

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          background: 'var(--bg-main)',
          gap: '1rem',
        }}
      >
        <div
          style={{
            background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
            color: '#ffffff',
            padding: '0.875rem',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-md)',
            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          }}
        >
          <Activity size={32} />
        </div>
        <div style={{ color: 'var(--secondary-700)', fontWeight: 600, fontSize: '0.9375rem' }}>
          Verifying secure healthcare session...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    // Safely redirect to user's assigned role dashboard
    if (user?.role === USER_ROLES.DOCTOR) {
      return <Navigate to="/doctor/dashboard" replace />;
    }
    if (user?.role === USER_ROLES.ADMIN) {
      return <Navigate to="/admin/dashboard" replace />;
    }
    if (user?.role === USER_ROLES.PATIENT) {
      return <Navigate to="/patient/dashboard" replace />;
    }
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
