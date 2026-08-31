import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LogIn, Activity, AlertCircle, Sparkles, User, Stethoscope, Shield } from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import { USER_ROLES } from '../../utils/constants';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login, isAuthenticated, user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If already authenticated, redirect to appropriate role dashboard
  useEffect(() => {
    if (isAuthenticated && !authLoading && user) {
      if (user.role === USER_ROLES.DOCTOR) {
        navigate('/doctor/dashboard', { replace: true });
      } else if (user.role === USER_ROLES.ADMIN) {
        navigate('/admin/dashboard', { replace: true });
      } else {
        navigate('/patient/dashboard', { replace: true });
      }
    }
  }, [isAuthenticated, authLoading, user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const authUser = await login({ email: email.trim(), password });
      
      // Determine redirection target
      const fromPath = location.state?.from?.pathname;
      let targetPath = '/patient/dashboard';

      if (authUser.role === USER_ROLES.DOCTOR) {
        targetPath = fromPath && fromPath.startsWith('/doctor') ? fromPath : '/doctor/dashboard';
      } else if (authUser.role === USER_ROLES.ADMIN) {
        targetPath = fromPath && fromPath.startsWith('/admin') ? fromPath : '/admin/dashboard';
      } else {
        targetPath = fromPath && fromPath.startsWith('/patient') ? fromPath : '/patient/dashboard';
      }

      navigate(targetPath, { replace: true });
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError(null);
  };

  return (
    <Card className="glass-panel" style={{ padding: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div
          style={{
            background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
            color: '#ffffff',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '0.75rem',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <Activity size={24} />
        </div>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem', fontWeight: 800 }}>Welcome Back</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--secondary-500)' }}>
          Sign in to access your healthcare portal
        </p>
      </div>

      {/* Demo Credentials Quick Fill Bar */}
      <div
        style={{
          background: 'var(--primary-50)',
          border: '1px solid var(--primary-100)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem',
          marginBottom: '1.25rem',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--primary-800)',
            marginBottom: '0.5rem',
          }}
        >
          <Sparkles size={13} /> Demo One-Click Fill:
        </div>
        <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            onClick={() => handleQuickFill('patient.john@example.com', 'PatientPass123!')}
          >
            <User size={12} /> Patient
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            onClick={() => handleQuickFill('dr.sarah@careai.com', 'DoctorPass123!')}
          >
            <Stethoscope size={12} /> Doctor
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            onClick={() => handleQuickFill('admin@careai.com', 'AdminPass123!')}
          >
            <Shield size={12} /> Admin
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            background: '#fff1f2',
            border: '1px solid #fecdd3',
            color: '#be123c',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '1.25rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Email Address</label>
          <input
            type="email"
            required
            className="form-input"
            placeholder="name@example.com"
            value={email}
            disabled={loading}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            type="password"
            required
            className="form-input"
            placeholder="••••••••"
            value={password}
            disabled={loading}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <Button
          type="submit"
          disabled={loading}
          variant="primary"
          style={{ width: '100%', marginTop: '0.5rem' }}
          icon={LogIn}
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </Button>
      </form>

      <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--secondary-500)' }}>
        Don't have an account?{' '}
        <Link to="/register" style={{ color: 'var(--primary-600)', fontWeight: 600, textDecoration: 'none' }}>
          Create an Account
        </Link>
      </div>
    </Card>
  );
}

export default LoginPage;
