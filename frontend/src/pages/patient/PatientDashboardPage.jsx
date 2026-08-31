import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Calendar,
  FileText,
  Search,
  ShieldCheck,
  UserCheck,
  AlertTriangle,
  Clock,
  ArrowRight,
  Stethoscope,
  Pill,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Video,
  ChevronRight,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import useAuth from '../../hooks/useAuth';
import dashboardService from '../../services/dashboardService';
import { formatDateTime, formatDate, formatCurrency } from '../../utils/formatters';

export function PatientDashboardPage() {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPatientDashboard();
  }, []);

  const loadPatientDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getPatientDashboard();
      setDashboardData(data);
    } catch (err) {
      console.error('Failed to load patient dashboard:', err);
      setError(err.message || 'Unable to connect to healthcare server.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="amber">Pending Confirmation</Badge>;
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

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'CRITICAL':
      case 'HIGH':
        return <Badge variant="rose">{risk} Risk</Badge>;
      case 'MODERATE':
        return <Badge variant="amber">Moderate Risk</Badge>;
      case 'LOW':
        return <Badge variant="blue">Low Risk</Badge>;
      case 'NONE':
        return <Badge variant="green">Clear / Safe</Badge>;
      default:
        return <Badge variant="slate">Unassessed</Badge>;
    }
  };

  const stats = dashboardData?.stats || {
    total_appointments: 0,
    upcoming_appointments: 0,
    completed_appointments: 0,
    active_prescriptions: 0,
  };

  const nextApp = dashboardData?.next_appointment;
  const recentRx = dashboardData?.recent_prescriptions || [];
  const aiSummary = dashboardData?.ai_safety_summary;
  const profileStatus = dashboardData?.medical_profile_status;

  return (
    <div className="animate-fade-in">
      {/* Welcome Banner */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>
              Welcome back, {user?.full_name || 'Patient'}
            </h1>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
              Real-time health overview, scheduled consultations, and AI-audited digital prescriptions.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/patient/prescriptions" className="btn btn-secondary">
              <FileText size={16} /> My Prescriptions ({stats.active_prescriptions})
            </Link>
            <Link to="/doctors" className="btn btn-primary">
              <Search size={16} /> Find & Book Doctor
            </Link>
          </div>
        </div>
      </div>

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
          <Button variant="secondary" style={{ marginLeft: 'auto', fontSize: '0.75rem' }} onClick={loadPatientDashboard}>
            Retry
          </Button>
        </div>
      )}

      {/* 4 Real-Time Overview Metrics Cards */}
      <div className="grid grid-cols-4 gap-4" style={{ marginBottom: '2rem' }}>
        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: 'var(--primary-100)', color: 'var(--primary-700)', padding: '0.75rem', borderRadius: '12px' }}>
              <Calendar size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Total Bookings</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.total_appointments}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.75rem', borderRadius: '12px' }}>
              <Clock size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Upcoming Visits</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.upcoming_appointments}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#dcfce7', color: '#15803d', padding: '0.75rem', borderRadius: '12px' }}>
              <CheckCircle size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Completed Visits</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.completed_appointments}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#fef3c7', color: '#b45309', padding: '0.75rem', borderRadius: '12px' }}>
              <FileText size={22} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Active Rx Vault</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.active_prescriptions}</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Grid: Nearest Upcoming Appointment + Recent Prescriptions */}
      <div className="grid grid-cols-2 gap-6" style={{ marginBottom: '2rem' }}>
        {/* Nearest Upcoming Consultation */}
        <Card
          title="Nearest Upcoming Consultation"
          subtitle="Your next scheduled doctor visit"
          headerAction={
            <Link to="/patient/appointments" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--primary-600)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
              All Visits <ArrowRight size={14} />
            </Link>
          }
        >
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
              Loading upcoming consultation...
            </div>
          ) : !nextApp ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
              <Calendar size={32} color="var(--secondary-400)" style={{ marginBottom: '0.75rem' }} />
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', marginBottom: '0.25rem' }}>No Upcoming Consultations</div>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem', marginBottom: '1.25rem' }}>
                You have no pending or confirmed appointments on your calendar.
              </p>
              <Link to="/doctors" className="btn btn-primary" style={{ padding: '0.45rem 1rem', fontSize: '0.8125rem' }}>
                Find a Doctor & Book Slot
              </Link>
            </div>
          ) : (
            <div
              style={{
                background: '#ffffff',
                border: '1px solid var(--secondary-200)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: '0.875rem', alignItems: 'center' }}>
                  <div
                    style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Stethoscope size={22} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--secondary-900)' }}>
                      {nextApp.doctor_name}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                      {nextApp.doctor_specialization} • Fee: {formatCurrency(nextApp.doctor_consultation_fee)}
                    </div>
                  </div>
                </div>
                {getStatusBadge(nextApp.status)}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.8125rem' }}>
                <div>
                  <span style={{ color: 'var(--secondary-500)', display: 'block', fontSize: '0.75rem' }}>Date & Time</span>
                  <strong>{formatDateTime(nextApp.scheduled_start)}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--secondary-500)', display: 'block', fontSize: '0.75rem' }}>Reason for Visit</span>
                  <span style={{ fontWeight: 600 }}>{nextApp.reason || 'General Consultation'}</span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {nextApp.meeting_link ? (
                  <a
                    href={nextApp.meeting_link}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-primary"
                    style={{ fontSize: '0.8125rem', padding: '0.4rem 0.875rem' }}
                  >
                    <Video size={14} /> Join Telehealth Room
                  </a>
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                    Clinic / In-Person Consultation
                  </span>
                )}
                <Link to="/patient/appointments" className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
                  Manage Visit
                </Link>
              </div>
            </div>
          )}
        </Card>

        {/* Recent Digital Prescriptions */}
        <Card
          title="Recent Digital Prescriptions"
          subtitle="Issued e-prescriptions with AI safety audit status"
          headerAction={
            <Link to="/patient/prescriptions" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--primary-600)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
              Vault <ArrowRight size={14} />
            </Link>
          }
        >
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
              Loading prescriptions...
            </div>
          ) : recentRx.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
              <FileText size={32} color="var(--secondary-400)" style={{ marginBottom: '0.75rem' }} />
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', marginBottom: '0.25rem' }}>No Prescriptions Recorded</div>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
                Your doctors will issue digital prescriptions directly after consultations.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recentRx.map((rx) => (
                <div
                  key={rx.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.875rem 1rem',
                    background: '#ffffff',
                    border: '1px solid var(--secondary-200)',
                    borderRadius: '8px',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>
                      {rx.diagnosis}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                      <span>{rx.doctor_name}</span>
                      <span>•</span>
                      <span>{formatDate(rx.created_at)}</span>
                      <span>•</span>
                      <span>{rx.medications_count} medication(s)</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {rx.has_ai_report ? (
                      getRiskBadge(rx.ai_risk_level)
                    ) : (
                      <Badge variant="slate">Not Audited</Badge>
                    )}
                    <Link
                      to="/patient/prescriptions"
                      className="btn btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Secondary Grid: AI Safety Summary + Medical Profile Status */}
      <div className="grid grid-cols-2 gap-6">
        {/* AI Safety Analysis Summary Card */}
        <Card
          title="AI Clinical Safety Overview"
          subtitle="Real-time multi-drug interaction and allergen screening metrics"
          className="glass-panel"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Sparkles size={20} color="#166534" />
                <div>
                  <strong style={{ color: '#166534', fontSize: '0.875rem' }}>AI Safety Guardian Active</strong>
                  <div style={{ fontSize: '0.75rem', color: '#15803d' }}>
                    Automated multi-drug, food interaction, and allergy contraindication checks
                  </div>
                </div>
              </div>
              <Badge variant="green">Operational</Badge>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid var(--secondary-200)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Audited Prescriptions</div>
                <div style={{ fontSize: '1.375rem', fontWeight: 800, marginTop: '2px' }}>
                  {aiSummary?.total_analyzed_prescriptions || 0}
                </div>
              </div>

              <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid var(--secondary-200)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>High Risk Findings</div>
                <div
                  style={{
                    fontSize: '1.375rem',
                    fontWeight: 800,
                    marginTop: '2px',
                    color: aiSummary?.high_risk_findings_count > 0 ? 'var(--accent-rose)' : 'var(--accent-green)',
                  }}
                >
                  {aiSummary?.high_risk_findings_count || 0}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8125rem', paddingTop: '0.5rem', borderTop: '1px solid var(--secondary-100)' }}>
              <span style={{ color: 'var(--secondary-500)' }}>Latest Audit Risk Assessment:</span>
              {getRiskBadge(aiSummary?.latest_overall_risk)}
            </div>
          </div>
        </Card>

        {/* Medical Profile Status */}
        <Card
          title="Clinical Health Profile Status"
          subtitle="Completeness indicator for patient sensitivities and emergency care"
          headerAction={
            <Link to="/patient/profile" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--primary-600)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
              Edit Profile <ChevronRight size={14} />
            </Link>
          }
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Profile Completeness:</span>
              {profileStatus?.is_complete ? (
                <Badge variant="green">Complete (100%)</Badge>
              ) : (
                <Badge variant="amber">Action Recommended</Badge>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--secondary-200)', fontSize: '0.8125rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Allergies Recorded:</span>
                <strong>{profileStatus?.allergies_count ? `${profileStatus.allergies_count} recorded` : 'None specified'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Chronic Conditions:</span>
                <strong>{profileStatus?.conditions_count ? `${profileStatus.conditions_count} recorded` : 'None specified'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Current Medications:</span>
                <strong>{profileStatus?.medications_count ? `${profileStatus.medications_count} recorded` : 'None specified'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Emergency Contact:</span>
                <strong>{profileStatus?.has_emergency_contact ? 'Verified' : 'Missing'}</strong>
              </div>
            </div>

            <Link to="/patient/profile" className="btn btn-secondary" style={{ width: '100%', textAlign: 'center', justifyContent: 'center', fontSize: '0.8125rem' }}>
              Update Health History & Allergies
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default PatientDashboardPage;
