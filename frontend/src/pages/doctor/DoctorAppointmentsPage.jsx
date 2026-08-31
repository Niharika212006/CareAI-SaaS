import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  User,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Activity,
  HeartPulse,
  Send,
  MessageSquare,
  ShieldCheck,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import appointmentService from '../../services/appointmentService';
import DoctorPatientSummaryModal from '../../components/doctor/DoctorPatientSummaryModal';
import { formatDateTime, formatAllergiesDisplay } from '../../utils/formatters';

export function DoctorAppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALL');
  const [actionMessage, setActionMessage] = useState(null);

  // Reject Modal State
  const [rejectingAppointment, setRejectingAppointment] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [submittingReject, setSubmittingReject] = useState(false);

  // Complete Modal State
  const [completingAppointment, setCompletingAppointment] = useState(null);
  const [doctorNotes, setDoctorNotes] = useState('');
  const [submittingComplete, setSubmittingComplete] = useState(false);

  // Patient Medical Summary Modal State
  const [viewingPatientSummaryId, setViewingPatientSummaryId] = useState(null);

  useEffect(() => {
    loadAppointments();
  }, []);

  const loadAppointments = async () => {
    try {
      setLoading(true);
      const data = await appointmentService.getMyDoctorAppointments();
      setAppointments(data || []);
    } catch (err) {
      console.error('Failed to load doctor appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (appointmentId) => {
    try {
      await appointmentService.confirmAppointment(appointmentId);
      setActionMessage('Appointment successfully confirmed.');
      loadAppointments();
    } catch (err) {
      console.error('Failed to confirm appointment:', err);
      alert(err.message || 'Error confirming appointment');
    }
  };

  const handleRejectSubmit = async (e) => {
    e.preventDefault();
    if (!rejectingAppointment) return;

    try {
      setSubmittingReject(true);
      await appointmentService.rejectAppointment(
        rejectingAppointment.id,
        rejectionReason.trim() || 'Schedule unavailable.'
      );
      setActionMessage('Consultation request declined.');
      setRejectingAppointment(null);
      setRejectionReason('');
      loadAppointments();
    } catch (err) {
      console.error('Failed to reject appointment:', err);
      alert(err.message || 'Error rejecting appointment');
    } finally {
      setSubmittingReject(false);
    }
  };

  const handleCompleteSubmit = async (e) => {
    e.preventDefault();
    if (!completingAppointment) return;

    try {
      setSubmittingComplete(true);
      await appointmentService.completeAppointment(
        completingAppointment.id,
        doctorNotes.trim() || 'Consultation concluded.'
      );
      setActionMessage('Consultation marked as completed.');
      setCompletingAppointment(null);
      setDoctorNotes('');
      loadAppointments();
    } catch (err) {
      console.error('Failed to complete appointment:', err);
      alert(err.message || 'Error marking appointment complete');
    } finally {
      setSubmittingComplete(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="amber">Pending Your Review</Badge>;
      case 'CONFIRMED':
        return <Badge variant="green">Confirmed</Badge>;
      case 'COMPLETED':
        return <Badge variant="blue">Completed</Badge>;
      case 'CANCELLED':
        return <Badge variant="slate">Cancelled</Badge>;
      case 'REJECTED':
        return <Badge variant="rose">Declined</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const filteredAppointments = appointments.filter((app) => {
    if (activeTab === 'ALL') return true;
    if (activeTab === 'CANCELLED') return app.status === 'CANCELLED' || app.status === 'REJECTED';
    return app.status === activeTab;
  });

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
          <Calendar size={28} color="var(--primary-700)" />
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>Patient Consultations & Schedule</h1>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Manage incoming consultation requests, review clinical histories, and record visit outcomes.
        </p>
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

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--secondary-200)', marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
        {[
          { id: 'ALL', label: 'All Consultations', count: appointments.length },
          { id: 'PENDING', label: 'Pending Requests', count: appointments.filter((a) => a.status === 'PENDING').length },
          { id: 'CONFIRMED', label: 'Confirmed Visits', count: appointments.filter((a) => a.status === 'CONFIRMED').length },
          { id: 'COMPLETED', label: 'Completed History', count: appointments.filter((a) => a.status === 'COMPLETED').length },
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

      {/* Consultations List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--secondary-500)' }}>
          Loading consultation schedule...
        </div>
      ) : filteredAppointments.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <Calendar size={40} color="var(--secondary-400)" style={{ marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.5rem' }}>No Consultations in this View</h3>
          <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem' }}>
            {activeTab === 'ALL' ? 'No patient appointments scheduled yet.' : `No consultations with status "${activeTab}".`}
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {filteredAppointments.map((app) => (
            <Card key={app.id} hover className="glass-panel">
              {/* Card Header & Actions */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <div
                    style={{
                      width: '46px',
                      height: '46px',
                      borderRadius: '12px',
                      background: 'var(--primary-100)',
                      color: 'var(--primary-700)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '1.125rem',
                    }}
                  >
                    {app.patient?.user?.full_name ? app.patient.user.full_name.charAt(0) : 'P'}
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '2px' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                        {app.patient?.user?.full_name || `Patient #${app.patient_id}`}
                      </h3>
                      {getStatusBadge(app.status)}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                      Email: {app.patient?.user?.email || 'N/A'} • Contact: {app.patient?.emergency_contact || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Workflow Actions */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                  <Button
                    variant="secondary"
                    style={{ padding: '0.4rem 0.75rem', fontSize: '0.8125rem' }}
                    onClick={() => setViewingPatientSummaryId(app.patient_id)}
                  >
                    <HeartPulse size={14} color="var(--primary-600)" /> Medical Summary
                  </Button>

                  {app.status === 'PENDING' && (
                    <>
                      <Button
                        variant="primary"
                        style={{ padding: '0.4rem 0.875rem', fontSize: '0.8125rem' }}
                        onClick={() => handleConfirm(app.id)}
                      >
                        <CheckCircle size={14} /> Accept & Confirm
                      </Button>
                      <Button
                        variant="danger"
                        style={{ padding: '0.4rem 0.875rem', fontSize: '0.8125rem' }}
                        onClick={() => {
                          setRejectingAppointment(app);
                          setRejectionReason('');
                        }}
                      >
                        <XCircle size={14} /> Decline
                      </Button>
                    </>
                  )}

                  {app.status === 'CONFIRMED' && (
                    <Button
                      variant="primary"
                      style={{ padding: '0.4rem 0.875rem', fontSize: '0.8125rem', background: 'var(--accent-emerald)' }}
                      onClick={() => {
                        setCompletingAppointment(app);
                        setDoctorNotes('');
                      }}
                    >
                      <CheckCircle size={14} /> Mark as Completed
                    </Button>
                  )}
                </div>
              </div>

              {/* Consultation Timing and Reason */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
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
                  <div style={{ color: 'var(--secondary-500)', marginBottom: '2px' }}>Reason for Visit</div>
                  <div style={{ fontWeight: 600 }}>{app.reason || app.reason_for_visit || 'General Consultation'}</div>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', marginBottom: '2px' }}>Patient Allergies / Blood Group</div>
                  <div style={{ fontWeight: 600, color: 'var(--accent-rose)' }}>
                    Allergies: {formatAllergiesDisplay(app.patient?.allergies)} • {app.patient?.blood_group || 'Blood: O+'}
                  </div>
                </div>
              </div>

              {/* Patient Notes */}
              {app.patient_notes && (
                <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-700)', marginBottom: '0.75rem', padding: '0.5rem 0.75rem', background: '#ffffff', borderRadius: '6px', border: '1px solid var(--secondary-200)' }}>
                  <strong>Patient Symptoms Note:</strong> {app.patient_notes}
                </div>
              )}

              {/* Recorded Outcome / Notes */}
              {app.status === 'COMPLETED' && app.doctor_notes && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '0.75rem', color: '#166534', fontSize: '0.8125rem' }}>
                  <strong>Physician Clinical Notes:</strong> {app.doctor_notes}
                </div>
              )}

              {app.status === 'REJECTED' && app.rejection_reason && (
                <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '8px', padding: '0.75rem', color: '#9f1239', fontSize: '0.8125rem' }}>
                  <strong>Decline Reason:</strong> {app.rejection_reason}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Reject Reason Modal */}
      {rejectingAppointment && (
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
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.75rem' }}>
              Decline Consultation Request
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--secondary-600)', marginBottom: '1.25rem' }}>
              Decline booking request for <strong>{rejectingAppointment.patient?.user?.full_name}</strong>.
            </p>

            <form onSubmit={handleRejectSubmit}>
              <div className="form-group">
                <label className="form-label">Reason / Feedback for Patient</label>
                <textarea
                  className="form-input"
                  rows={3}
                  required
                  placeholder="e.g. Schedule clash with clinical rounds; please re-book for tomorrow afternoon."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <Button variant="secondary" onClick={() => setRejectingAppointment(null)} disabled={submittingReject}>
                  Cancel
                </Button>
                <Button type="submit" variant="danger" disabled={submittingReject}>
                  {submittingReject ? 'Declining...' : 'Confirm Decline'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Complete Notes Modal */}
      {completingAppointment && (
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
              maxWidth: '480px',
              width: '100%',
              boxShadow: 'var(--shadow-xl)',
              overflow: 'hidden',
              padding: '1.5rem',
            }}
          >
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Complete Clinical Consultation
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--secondary-600)', marginBottom: '1.25rem' }}>
              Record final clinical observations and diagnostic instructions for <strong>{completingAppointment.patient?.user?.full_name}</strong>.
            </p>

            <form onSubmit={handleCompleteSubmit}>
              <div className="form-group">
                <label className="form-label">Clinical Consultation Summary & Instructions</label>
                <textarea
                  className="form-input"
                  rows={4}
                  required
                  placeholder="e.g. Patient presented with seasonal allergies. Advised oral antihistamines, adequate rest, and follow-up in 10 days if symptoms persist."
                  value={doctorNotes}
                  onChange={(e) => setDoctorNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <Button variant="secondary" onClick={() => setCompletingAppointment(null)} disabled={submittingComplete}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={submittingComplete}>
                  {submittingComplete ? 'Saving...' : 'Conclude & Mark Completed'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Patient Medical Summary Modal */}
      {viewingPatientSummaryId && (
        <DoctorPatientSummaryModal
          patientId={viewingPatientSummaryId}
          onClose={() => setViewingPatientSummaryId(null)}
        />
      )}
    </div>
  );
}

export default DoctorAppointmentsPage;
