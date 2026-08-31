import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  Users,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Stethoscope,
  Activity,
  Calendar,
  Clock,
  Search,
  Sparkles,
  FileText,
  AlertCircle,
  UserCheck,
  Zap,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import doctorService from '../../services/doctorService';
import dashboardService from '../../services/dashboardService';
import { formatDateTime, formatDate } from '../../utils/formatters';

export function AdminDashboardPage() {
  const [dashboardData, setDashboardData] = useState(null);
  const [pendingDoctors, setPendingDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  useEffect(() => {
    loadAdminDashboard();
  }, []);

  const loadAdminDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dash, pending] = await Promise.all([
        dashboardService.getAdminDashboard(),
        doctorService.getPendingDoctors().catch(() => []),
      ]);
      setDashboardData(dash);
      setPendingDoctors(pending || []);
    } catch (err) {
      console.error('Failed to load admin dashboard data:', err);
      setError(err.message || 'Failed to load system administration dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (doctorId, status) => {
    try {
      await doctorService.reviewDoctor(doctorId, {
        approval_status: status,
        rejection_reason: status === 'REJECTED' ? 'Credentials could not be verified' : null,
      });
      setActionMessage(`Doctor application ${status.toLowerCase()} successfully.`);
      loadAdminDashboard();
    } catch (err) {
      console.error('Review action failed:', err);
    }
  };

  const platformStats = dashboardData?.platform_stats || {
    total_users: 0,
    total_patients: 0,
    total_doctors: 0,
    approved_doctors: 0,
    pending_doctor_approvals: 0,
    rejected_doctors: 0,
    total_appointments: 0,
    completed_appointments: 0,
    cancelled_appointments: 0,
    total_prescriptions: 0,
    total_ai_analyses: 0,
  };

  const doctorSummary = dashboardData?.doctor_summary || { pending_count: 0, approved_count: 0, rejected_count: 0 };
  const apptSummary = dashboardData?.appointment_summary || {
    pending_count: 0,
    confirmed_count: 0,
    completed_count: 0,
    cancelled_count: 0,
    rejected_count: 0,
  };
  const aiMetrics = dashboardData?.ai_safety_metrics || {
    total_reports: 0,
    critical_risk_count: 0,
    high_risk_count: 0,
    moderate_risk_count: 0,
    low_risk_count: 0,
    none_risk_count: 0,
    total_findings_detected: 0,
  };
  const recentActivity = dashboardData?.recent_activity || [];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
          <h1 style={{ fontSize: '1.875rem' }}>System Administration Portal</h1>
          <Badge variant="rose">Superuser</Badge>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Real-time system telemetry, clinical credential moderation, privacy-conscious audit logs, and AI safety metrics.
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

      {error && (
        <div
          style={{
            background: '#fff1f2',
            border: '1px solid #fecdd3',
            color: '#be123c',
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertCircle size={18} />
          <span>{error}</span>
          <Button variant="secondary" style={{ marginLeft: 'auto', fontSize: '0.75rem' }} onClick={loadAdminDashboard}>
            Retry
          </Button>
        </div>
      )}

      {/* Platform Overview Metrics Cards */}
      <div className="grid grid-cols-4 gap-4" style={{ marginBottom: '2rem' }}>
        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: 'var(--primary-100)', color: 'var(--primary-700)', padding: '0.75rem', borderRadius: '12px' }}>
              <Users size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Total Accounts</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{platformStats.total_users}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.75rem', borderRadius: '12px' }}>
              <Stethoscope size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Verified Doctors</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{platformStats.approved_doctors} / {platformStats.total_doctors}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#fef3c7', color: '#b45309', padding: '0.75rem', borderRadius: '12px' }}>
              <Calendar size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Total Consultations</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{platformStats.total_appointments}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#dcfce7', color: '#15803d', padding: '0.75rem', borderRadius: '12px' }}>
              <Sparkles size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>AI Safety Audits</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{platformStats.total_ai_analyses}</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Grid: Doctor Verification Queue & Platform Activity */}
      <div className="grid grid-cols-2 gap-6" style={{ marginBottom: '2rem' }}>
        {/* Doctor Verification Queue */}
        <Card
          title="Doctor Credential Verification Queue"
          subtitle="Review medical license credentials before allowing clinical consultations"
          headerAction={
            <Badge variant={pendingDoctors.length > 0 ? 'amber' : 'green'}>
              {pendingDoctors.length} Awaiting Review
            </Badge>
          }
        >
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
              Loading pending verification applications...
            </div>
          ) : pendingDoctors.length === 0 ? (
            <div
              style={{
                padding: '2.5rem 1rem',
                textAlign: 'center',
                background: '#f8fafc',
                borderRadius: '8px',
                border: '1px dashed var(--secondary-200)',
              }}
            >
              <CheckCircle size={32} color="var(--primary-600)" style={{ marginBottom: '0.5rem' }} />
              <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>No Pending Applications</div>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
                All physician credential submissions have been moderated.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              {pendingDoctors.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.875rem 1rem',
                    border: '1px solid var(--secondary-200)',
                    borderRadius: 'var(--radius-md)',
                    background: '#ffffff',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9375rem' }}>
                        {doc.user?.full_name || `Doctor ID #${doc.id}`}
                      </span>
                      <Badge variant="amber">Pending</Badge>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                      Specialization: <strong>{doc.specialization}</strong> • License: <strong>{doc.license_number}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Button
                      variant="primary"
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                      onClick={() => handleReview(doc.id, 'APPROVED')}
                    >
                      <CheckCircle size={14} /> Approve
                    </Button>
                    <Button
                      variant="danger"
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                      onClick={() => handleReview(doc.id, 'REJECTED')}
                    >
                      <XCircle size={14} /> Reject
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Real-Time Platform Activity Audit Feed */}
        <Card
          title="Platform Activity Audit Trail"
          subtitle="Real-time chronological log of registrations, applications, and consultations"
        >
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
              Loading platform audit log...
            </div>
          ) : recentActivity.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
              <Clock size={32} color="var(--secondary-400)" style={{ marginBottom: '0.5rem' }} />
              <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>No Platform Activity Recorded</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '340px', overflowY: 'auto' }}>
              {recentActivity.map((act, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.75rem',
                    padding: '0.65rem 0.875rem',
                    background: '#f8fafc',
                    border: '1px solid var(--secondary-200)',
                    borderRadius: '8px',
                  }}
                >
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      background:
                        act.event_type === 'USER_REGISTERED'
                          ? '#e0f2fe'
                          : act.event_type === 'DOCTOR_APPLICATION'
                          ? '#fef3c7'
                          : '#dcfce7',
                      color:
                        act.event_type === 'USER_REGISTERED'
                          ? '#0369a1'
                          : act.event_type === 'DOCTOR_APPLICATION'
                          ? '#b45309'
                          : '#15803d',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: '2px',
                    }}
                  >
                    {act.event_type === 'USER_REGISTERED' ? (
                      <UserCheck size={14} />
                    ) : act.event_type === 'DOCTOR_APPLICATION' ? (
                      <Stethoscope size={14} />
                    ) : (
                      <Calendar size={14} />
                    )}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ fontSize: '0.8125rem' }}>{act.title}</strong>
                      <span style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)' }}>
                        {formatDateTime(act.timestamp)}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--secondary-600)', margin: '2px 0 0 0' }}>
                      {act.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Secondary Row: AI Safety Telemetry & Consultation Status Breakdown */}
      <div className="grid grid-cols-2 gap-6">
        {/* AI Safety Platform Telemetry */}
        <Card
          title="AI Clinical Safety Platform Telemetry"
          subtitle="Aggregated risk level distribution and interaction hazard detection"
          className="glass-panel"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', textAlign: 'center' }}>
              <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.625rem 0.25rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700 }}>CRITICAL</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{aiMetrics.critical_risk_count}</div>
              </div>
              <div style={{ background: '#ffe4e6', color: '#be123c', padding: '0.625rem 0.25rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700 }}>HIGH</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{aiMetrics.high_risk_count}</div>
              </div>
              <div style={{ background: '#fef3c7', color: '#b45309', padding: '0.625rem 0.25rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700 }}>MODERATE</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{aiMetrics.moderate_risk_count}</div>
              </div>
              <div style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.625rem 0.25rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700 }}>LOW</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{aiMetrics.low_risk_count}</div>
              </div>
              <div style={{ background: '#dcfce7', color: '#15803d', padding: '0.625rem 0.25rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.6875rem', fontWeight: 700 }}>NONE/CLEAR</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800 }}>{aiMetrics.none_risk_count}</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--secondary-200)', fontSize: '0.8125rem' }}>
              <span style={{ color: 'var(--secondary-600)' }}>Total Clinical Hazards Intercepted:</span>
              <strong style={{ fontSize: '1rem', color: 'var(--primary-700)' }}>{aiMetrics.total_findings_detected} Hazards</strong>
            </div>
          </div>
        </Card>

        {/* Consultation Breakdown */}
        <Card
          title="Consultation Volume Breakdown"
          subtitle="Platform appointment lifecycle distribution"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem', fontSize: '0.8125rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0', borderBottom: '1px solid var(--secondary-100)' }}>
              <span style={{ color: 'var(--secondary-600)' }}>Pending Confirmation:</span>
              <strong>{apptSummary.pending_count}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0', borderBottom: '1px solid var(--secondary-100)' }}>
              <span style={{ color: 'var(--secondary-600)' }}>Confirmed & Scheduled:</span>
              <strong>{apptSummary.confirmed_count}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0', borderBottom: '1px solid var(--secondary-100)' }}>
              <span style={{ color: 'var(--secondary-600)' }}>Successfully Completed:</span>
              <strong style={{ color: 'var(--accent-green)' }}>{apptSummary.completed_count}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0' }}>
              <span style={{ color: 'var(--secondary-600)' }}>Cancelled / Declined:</span>
              <strong style={{ color: 'var(--secondary-500)' }}>{apptSummary.cancelled_count + apptSummary.rejected_count}</strong>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default AdminDashboardPage;
