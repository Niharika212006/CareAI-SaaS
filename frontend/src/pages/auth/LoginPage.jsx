import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LogIn, Activity, AlertCircle, RefreshCw } from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import { USER_ROLES, BACKEND_ROOT_URL } from '../../utils/constants';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [connectingLong, setConnectingLong] = useState(false);
  const timerRef = useRef(null);

  const { login, isAuthenticated, user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Warm up Render cloud backend on mount to avoid cold-start delays
  useEffect(() => {
    fetch(`${BACKEND_ROOT_URL}/health`, { method: 'GET', mode: 'cors' }).catch(() => {});
  }, []);

  // Monitor long-running connection (Render free tier cold starts take 30-45s)
  useEffect(() => {
    if (loading) {
      timerRef.current = setTimeout(() => {
        setConnectingLong(true);
      }, 3000);
    } else {
      if (timerRef.current) clearTimeout(timerRef.current);
      setConnectingLong(false);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [loading]);

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
    if (e && e.preventDefault) e.preventDefault();
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
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ flex: 1 }}>
              <span>{error}</span>
              {error.includes('backend server') || error.includes('waking up') ? (
                <div style={{ marginTop: '0.5rem' }}>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    className="btn btn-secondary"
                    style={{
                      padding: '0.3rem 0.75rem',
                      fontSize: '0.8rem',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                    }}
                  >
                    <RefreshCw size={14} /> Retry Login
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {connectingLong && (
        <div
          style={{
            background: '#f0f9ff',
            border: '1px solid #bae6fd',
            color: '#0369a1',
            padding: '0.65rem 0.9rem',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.825rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <RefreshCw size={16} className="animate-spin" style={{ animation: 'spin 1.5s linear infinite' }} />
          <span>Waking up cloud backend (Render free tier takes ~30-45s)...</span>
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
          {loading ? (connectingLong ? 'Connecting to Cloud Backend...' : 'Authenticating...') : 'Sign In'}
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
