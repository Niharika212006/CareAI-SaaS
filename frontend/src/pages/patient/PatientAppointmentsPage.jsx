import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Clock,
  User,
  Stethoscope,
  XCircle,
  CheckCircle,
  AlertCircle,
  Plus,
  FileText,
  Building,
  DollarSign,
  AlertTriangle,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import appointmentService from '../../services/appointmentService';
import { formatDateTime, formatCurrency } from '../../utils/formatters';

export function PatientAppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALL');
  const [actionMessage, setActionMessage] = useState(null);

  // Cancel Modal State
  const [cancellingAppointment, setCancellingAppointment] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [submittingCancel, setSubmittingCancel] = useState(false);
  const [cancelError, setCancelError] = useState(null);

  useEffect(() => {
    loadAppointments();
  }, []);

  const loadAppointments = async () => {
    try {
      setLoading(true);
      const data = await appointmentService.getMyPatientAppointments();
      setAppointments(data || []);
    } catch (err) {
      console.error('Failed to load appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubmit = async (e) => {
    e.preventDefault();
    if (!cancellingAppointment) return;

    try {
      setSubmittingCancel(true);
      setCancelError(null);
      await appointmentService.cancelAppointment(
        cancellingAppointment.id,
        cancelReason.trim() || 'Cancelled by patient'
      );
      setActionMessage('Appointment successfully cancelled.');
      setCancellingAppointment(null);
      setCancelReason('');
      loadAppointments();
    } catch (err) {
      console.error('Cancel failed:', err);
      setCancelError(err.message || 'Failed to cancel appointment.');
    } finally {
      setSubmittingCancel(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="amber">Pending Doctor Confirmation</Badge>;
      case 'CONFIRMED':
        return <Badge variant="green">Confirmed</Badge>;
      case 'COMPLETED':
        return <Badge variant="blue">Completed</Badge>;
      case 'CANCELLED':
        return <Badge variant="slate">Cancelled</Badge>;
      case 'REJECTED':
        return <Badge variant="rose">Declined by Doctor</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const filteredAppointments = appointments.filter((app) => {
    if (activeTab === 'ALL') return true;
    return app.status === activeTab;
  });

  return (
    <div className="animate-fade-in">
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
            <Calendar size={28} color="var(--primary-700)" />
            <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>My Medical Consultations</h1>
          </div>
          <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
            Track appointment status, review scheduled consultations, or cancel upcoming visits.
          </p>
        </div>

        <Link to="/doctors" className="btn btn-primary">
          <Plus size={16} /> Book New Consultation
        </Link>
      </div>

      {actionMessage && (
        <div
          style={{
            background: '#dcfce7',
            border: '1px solid #bbf7d0',
            color: '#15803d',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <CheckCircle size={16} />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--secondary-200)', marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
        {[
          { id: 'ALL', label: 'All Consultations', count: appointments.length },
          { id: 'PENDING', label: 'Pending', count: appointments.filter((a) => a.status === 'PENDING').length },
          { id: 'CONFIRMED', label: 'Confirmed', count: appointments.filter((a) => a.status === 'CONFIRMED').length },
          { id: 'COMPLETED', label: 'Completed', count: appointments.filter((a) => a.status === 'COMPLETED').length },
          { id: 'CANCELLED', label: 'Cancelled / Declined', count: appointments.filter((a) => a.status === 'CANCELLED' || a.status === 'REJECTED').length },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--primary-600)' : '2px solid transparent',
              background: activeTab === tab.id ? 'var(--primary-50)' : 'transparent',
              color: activeTab === tab.id ? 'var(--primary-800)' : 'var(--secondary-600)',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              whiteSpace: 'nowrap',
            }}
          >
            <span>{tab.label}</span>
            <span
              style={{
                fontSize: '0.75rem',
                padding: '2px 6px',
                borderRadius: '10px',
                background: activeTab === tab.id ? 'var(--primary-200)' : 'var(--secondary-200)',
                color: activeTab === tab.id ? 'var(--primary-900)' : 'var(--secondary-700)',
              }}
            >
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Appointments List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--secondary-500)' }}>
          Loading your appointments...
        </div>
      ) : filteredAppointments.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <Calendar size={40} color="var(--secondary-400)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.5rem' }}>No Consultations Found</h3>
          <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
            {activeTab === 'ALL'
              ? "You haven't scheduled any consultations yet."
              : `No appointments with status "${activeTab}".`}
          </p>
          <Link to="/doctors" className="btn btn-primary">
            Find an Approved Doctor
          </Link>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredAppointments.map((app) => (
            <Card key={app.id} hover className="glass-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '12px',
                      background: 'var(--primary-100)',
                      color: 'var(--primary-700)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '1.25rem',
                      flexShrink: 0,
                    }}
                  >
                    <Stethoscope size={22} />
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.25rem' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                        Dr. {app.doctor?.user?.full_name || `Doctor #${app.doctor_id}`}
                      </h3>
                      {getStatusBadge(app.status)}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--primary-700)', fontWeight: 600 }}>
                      {app.doctor?.specialization || 'Medical Specialist'} • {app.doctor?.hospital_affiliation || 'CareAI Network'}
                    </div>
                  </div>
                </div>

                {/* Status action buttons */}
                {(app.status === 'PENDING' || app.status === 'CONFIRMED') && (
                  <Button
                    variant="danger"
                    style={{ padding: '0.4rem 0.875rem', fontSize: '0.8125rem' }}
                    onClick={() => {
                      setCancellingAppointment(app);
                      setCancelError(null);
                      setCancelReason('');
                    }}
                  >
                    <XCircle size={14} /> Cancel Appointment
                  </Button>
                )}
              </div>

              {/* Consultation Details Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '1rem',
                  padding: '0.875rem 1rem',
                  background: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--secondary-200)',
                  marginBottom: '1rem',
                  fontSize: '0.8125rem',
                }}
              >
                <div>
                  <div style={{ color: 'var(--secondary-500)', marginBottom: '2px' }}>Scheduled Date & Time</div>
                  <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} color="var(--primary-600)" />
                    {formatDateTime(app.scheduled_start)}
                  </div>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', marginBottom: '2px' }}>Consultation Reason</div>
                  <div style={{ fontWeight: 600 }}>{app.reason || app.reason_for_visit || 'General Consultation'}</div>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', marginBottom: '2px' }}>Consultation Fee</div>
                  <div style={{ fontWeight: 700, color: 'var(--secondary-900)' }}>
                    {formatCurrency(app.doctor?.consultation_fee || 0)}
                  </div>
                </div>
              </div>

              {/* Additional Context Notices (Rejection, Cancellation, Clinical Summary) */}
              {app.status === 'REJECTED' && app.rejection_reason && (
                <div
                  style={{
                    background: '#fff1f2',
                    border: '1px solid #fecdd3',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    color: '#9f1239',
                    fontSize: '0.8125rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <AlertCircle size={16} />
                  <span>
                    <strong>Doctor's Reason for Declining:</strong> {app.rejection_reason}
                  </span>
                </div>
              )}

              {app.status === 'CANCELLED' && app.cancellation_reason && (
                <div
                  style={{
                    background: '#f1f5f9',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    color: 'var(--secondary-700)',
                    fontSize: '0.8125rem',
                  }}
                >
                  <strong>Cancellation Reason:</strong> {app.cancellation_reason}
                </div>
              )}

              {app.status === 'COMPLETED' && app.doctor_notes && (
                <div
                  style={{
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    color: '#166534',
                    fontSize: '0.8125rem',
                  }}
                >
                  <strong>Physician Clinical Notes:</strong> {app.doctor_notes}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Cancel Appointment Confirmation Modal */}
      {cancellingAppointment && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1rem',
          }}
        >
          <div
            className="animate-fade-in"
            style={{
              backgroundColor: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              maxWidth: '460px',
              width: '100%',
              boxShadow: 'var(--shadow-xl)',
              overflow: 'hidden',
              padding: '1.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--accent-rose)' }}>
              <AlertTriangle size={24} />
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                Cancel Consultation
              </h3>
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--secondary-600)', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              Are you sure you want to cancel your consultation with <strong>Dr. {cancellingAppointment.doctor?.user?.full_name}</strong> scheduled for{' '}
              <strong>{formatDateTime(cancellingAppointment.scheduled_start)}</strong>?
            </p>

            {cancelError && (
              <div
                style={{
                  background: '#fff1f2',
                  border: '1px solid #fecdd3',
                  color: '#9f1239',
                  padding: '0.625rem',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '1rem',
                  fontSize: '0.8125rem',
                }}
              >
                {cancelError}
              </div>
            )}

            <form onSubmit={handleCancelSubmit}>
              <div className="form-group">
                <label className="form-label">Reason for Cancellation (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Schedule clash, Feeling better"
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <Button variant="secondary" onClick={() => setCancellingAppointment(null)} disabled={submittingCancel}>
                  Keep Appointment
                </Button>
                <Button type="submit" variant="danger" disabled={submittingCancel}>
                  {submittingCancel ? 'Cancelling...' : 'Confirm Cancellation'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default PatientAppointmentsPage;
