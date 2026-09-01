import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LogIn, Activity, AlertCircle } from 'lucide-react';
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
      } else if (user.role === USER_ROLES.LAB_TECHNICIAN) {
        navigate('/lab/dashboard', { replace: true });
      } else if (user.role === USER_ROLES.PHARMACY_STAFF) {
        navigate('/pharmacy/dashboard', { replace: true });
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
      } else if (authUser.role === USER_ROLES.LAB_TECHNICIAN) {
        targetPath = fromPath && fromPath.startsWith('/lab') ? fromPath : '/lab/dashboard';
      } else if (authUser.role === USER_ROLES.PHARMACY_STAFF) {
        targetPath = fromPath && fromPath.startsWith('/pharmacy') ? fromPath : '/pharmacy/dashboard';
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

  return (
    <Card className="glass-panel" style={{ padding: '2.5rem 2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
        <div
          style={{
            background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
            color: '#ffffff',
            width: '52px',
            height: '52px',
            borderRadius: '14px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1rem',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <Activity size={26} />
        </div>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.375rem', fontWeight: 800 }}>Welcome Back</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--secondary-500)' }}>
          Sign in to access your healthcare portal
        </p>
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
            marginBottom: '1.5rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group" style={{ marginBottom: '1.25rem' }}>
          <label className="form-label" style={{ marginBottom: '0.375rem', display: 'block' }}>Email Address</label>
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

        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label className="form-label" style={{ marginBottom: '0.375rem', display: 'block' }}>Password</label>
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
          style={{ width: '100%', padding: '0.75rem' }}
          icon={LogIn}
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </Button>
      </form>

      <div style={{ marginTop: '1.75rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--secondary-500)' }}>
        Don't have an account?{' '}
        <Link to="/register" style={{ color: 'var(--primary-600)', fontWeight: 600, textDecoration: 'none' }}>
          Create an Account
        </Link>
      </div>
    </Card>
  );
}

export default LoginPage;
