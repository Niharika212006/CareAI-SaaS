import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, LogOut, User as UserIcon, Shield, Stethoscope, HeartPulse } from 'lucide-react';
import useAuth from '../../hooks/useAuth';
import Badge from './Badge';
import NotificationBell from './NotificationBell';

export function Navbar() {
  const { user, isAuthenticated, logout, isPatient, isDoctor, isAdmin, isLabTechnician, isPharmacyStaff } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getRoleBadge = () => {
    if (isAdmin) return <Badge variant="rose">Admin</Badge>;
    if (isDoctor) return <Badge variant="blue">Doctor</Badge>;
    if (isLabTechnician) return <Badge variant="purple">Lab Tech</Badge>;
    if (isPharmacyStaff) return <Badge variant="amber">Pharmacy</Badge>;
    return <Badge variant="teal">Patient</Badge>;
  };

  const getDashboardPath = () => {
    if (isAdmin) return '/admin/dashboard';
    if (isDoctor) return '/doctor/dashboard';
    if (isLabTechnician) return '/lab/dashboard';
    if (isPharmacyStaff) return '/pharmacy/dashboard';
    return '/patient/dashboard';
  };

  return (
    <header
      style={{
        background: '#ffffff',
        borderBottom: '1px solid var(--secondary-200)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        height: '64px',
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <div
        className="page-container"
        style={{
          padding: '0 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          width: '100%',
        }}
      >
        {/* Brand Logo */}
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            textDecoration: 'none',
            color: 'var(--secondary-900)',
          }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
              color: '#ffffff',
              padding: '0.5rem',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Activity size={20} />
          </div>
          <div>
            <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: '1.2rem', letterSpacing: '-0.02em' }}>
              CareAI <span style={{ color: 'var(--primary-600)' }}>SaaS</span>
            </span>
          </div>
        </Link>

        {/* Navigation / Actions */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          {isAuthenticated ? (
            <>
              <Link
                to={getDashboardPath()}
                style={{
                  textDecoration: 'none',
                  color: 'var(--secondary-700)',
                  fontWeight: 600,
                  fontSize: '0.875rem',
                }}
              >
                Dashboard
              </Link>

              <NotificationBell />
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingLeft: '0.75rem', borderLeft: '1px solid var(--secondary-200)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--secondary-900)' }}>
                    {user?.full_name || user?.email}
                  </span>
                  <div style={{ marginTop: '2px' }}>{getRoleBadge()}</div>
                </div>

                <button
                  onClick={handleLogout}
                  title="Log out"
                  className="btn btn-secondary"
                  style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)' }}
                >
                  <LogOut size={16} />
                </button>
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Link to="/login" className="btn btn-secondary" style={{ padding: '0.5rem 1rem' }}>
                Sign In
              </Link>
              <Link to="/register" className="btn btn-primary" style={{ padding: '0.5rem 1rem' }}>
                Get Started
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Navbar;
