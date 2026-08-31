import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Activity, AlertCircle } from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import { USER_ROLES } from '../../utils/constants';

export function RegisterPage() {
  const [countryCode, setCountryCode] = useState('+91');
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    role: USER_ROLES.PATIENT,
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { register, isAuthenticated, user, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // If already authenticated, redirect to appropriate role dashboard
  React.useEffect(() => {
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

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const payload = {
        ...formData,
        phone_number: formData.phone_number?.trim()
          ? (formData.phone_number.trim().startsWith('+')
              ? formData.phone_number.trim()
              : `${countryCode} ${formData.phone_number.trim()}`)
          : null,
      };
      const regUser = await register(payload);
      if (regUser.role === USER_ROLES.DOCTOR) {
        navigate('/doctor/dashboard', { replace: true });
      } else if (regUser.role === USER_ROLES.ADMIN) {
        navigate('/admin/dashboard', { replace: true });
      } else if (regUser.role === USER_ROLES.LAB_TECHNICIAN) {
        navigate('/lab/dashboard', { replace: true });
      } else if (regUser.role === USER_ROLES.PHARMACY_STAFF) {
        navigate('/pharmacy/dashboard', { replace: true });
      } else {
        navigate('/patient/dashboard', { replace: true });
      }
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
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
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Create an Account</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--secondary-500)' }}>
          Join the AI Healthcare SaaS ecosystem
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
            marginBottom: '1.25rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">I am registering as</label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <button
              type="button"
              className={`btn ${formData.role === USER_ROLES.PATIENT ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFormData((p) => ({ ...p, role: USER_ROLES.PATIENT }))}
            >
              Patient
            </button>
            <button
              type="button"
              className={`btn ${formData.role === USER_ROLES.DOCTOR ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFormData((p) => ({ ...p, role: USER_ROLES.DOCTOR }))}
            >
              Doctor
            </button>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Full Name</label>
          <input
            type="text"
            name="full_name"
            required
            className="form-input"
            placeholder={formData.role === USER_ROLES.DOCTOR ? 'Dr. Jane Smith' : 'Jane Smith'}
            value={formData.full_name}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Email Address</label>
          <input
            type="email"
            name="email"
            required
            className="form-input"
            placeholder="jane@example.com"
            value={formData.email}
            onChange={handleChange}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Phone Number (Optional)</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <select
              value={countryCode}
              onChange={(e) => setCountryCode(e.target.value)}
              className="form-input"
              style={{ width: '100px', fontWeight: 600, paddingLeft: '0.5rem', paddingRight: '0.5rem' }}
            >
              <option value="+91">+91 (IN)</option>
              <option value="+1">+1 (US)</option>
              <option value="+44">+44 (UK)</option>
              <option value="+61">+61 (AU)</option>
              <option value="+971">+971 (AE)</option>
            </select>
            <input
              type="tel"
              name="phone_number"
              className="form-input"
              style={{ flex: 1 }}
              placeholder="98765 43210"
              value={formData.phone_number}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            type="password"
            name="password"
            required
            className="form-input"
            placeholder="••••••••"
            value={formData.password}
            onChange={handleChange}
          />
        </div>

        <Button
          type="submit"
          disabled={loading}
          variant="primary"
          style={{ width: '100%', marginTop: '0.5rem' }}
          icon={UserPlus}
        >
          {loading ? 'Creating Account...' : 'Complete Registration'}
        </Button>
      </form>

      <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--secondary-500)' }}>
        Already have an account?{' '}
        <Link to="/login" style={{ color: 'var(--primary-600)', fontWeight: 600, textDecoration: 'none' }}>
          Sign In
        </Link>
      </div>
    </Card>
  );
}

export default RegisterPage;
