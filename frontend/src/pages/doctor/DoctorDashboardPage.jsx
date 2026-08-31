import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Stethoscope,
  Calendar,
  FileText,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Send,
  ArrowRight,
  CheckCircle,
  Users,
  AlertCircle,
  Video,
  ChevronRight,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import useAuth from '../../hooks/useAuth';
import doctorService from '../../services/doctorService';
import appointmentService from '../../services/appointmentService';
import dashboardService from '../../services/dashboardService';
import aiService from '../../services/aiService';
import { formatDateTime, formatDate } from '../../utils/formatters';

export function DoctorDashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  // Quick AI Test Sandbox State
  const [testMeds, setTestMeds] = useState('Aspirin, Warfarin, Ciprofloxacin');
  const [testAllergies, setTestAllergies] = useState('Penicillin');
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    loadDoctorDashboard();
  }, []);

  const loadDoctorDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [prof, data] = await Promise.all([
        doctorService.getMyProfile().catch(() => null),
        dashboardService.getDoctorDashboard(),
      ]);
      setProfile(prof);
      setDashboardData(data);
    } catch (err) {
      console.error('Failed to load doctor dashboard data:', err);
      setError(err.message || 'Failed to load doctor operational dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (appointmentId) => {
    try {
      await appointmentService.confirmAppointment(appointmentId);
      setActionMessage('Consultation booking confirmed.');
      loadDoctorDashboard();
    } catch (err) {
      console.error('Confirm failed:', err);
    }
  };

  const handleRunAiCheck = async () => {
    setAiLoading(true);
    try {
      const medications = testMeds.split(',').map((m) => m.trim()).filter(Boolean);
      const allergies = testAllergies.split(',').map((a) => a.trim()).filter(Boolean);
      const res = await aiService.analyzeInteractions({
        medications,
        patient_allergies: allergies,
      });
      setAiResult(res);
    } catch (err) {
      console.error('AI check error:', err);
    } finally {
      setAiLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="amber">Pending</Badge>;
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

  const stats = dashboardData?.stats || {
    today_appointments: 0,
    upcoming_appointments: 0,
    completed_consultations: 0,
    total_patients: 0,
    prescriptions_issued: 0,
  };

  const todaySchedule = dashboardData?.today_schedule || [];
  const pendingActions = dashboardData?.pending_actions || {
    pending_appointment_requests: 0,
    confirmed_awaiting_consultation: 0,
    completed_awaiting_prescription: 0,
  };
  const availability = dashboardData?.availability_summary;
  const recentActivity = dashboardData?.recent_patient_activity || [];

  return (
    <div className="animate-fade-in">
      {/* Welcome & Approval Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
              <h1 style={{ fontSize: '1.875rem' }}>Dr. {user?.full_name || 'Practitioner'}</h1>
              {profile?.approval_status === 'APPROVED' ? (
                <Badge variant="green">Verified Physician</Badge>
              ) : profile?.approval_status === 'REJECTED' ? (
                <Badge variant="rose">Credentials Rejected</Badge>
              ) : (
                <Badge variant="amber">Verification Pending</Badge>
              )}
            </div>
            <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
              Specialization: <strong>{profile?.specialization || 'General Practice'}</strong> • License: {profile?.license_number || 'Pending'}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/doctor/availability" className="btn btn-secondary">
              <Clock size={16} /> Schedule & Hours
            </Link>
            <Link to="/doctor/prescriptions" className="btn btn-secondary">
              <FileText size={16} /> Rx Studio ({stats.prescriptions_issued})
            </Link>
            <Link to="/doctor/appointments" className="btn btn-primary">
              <Calendar size={16} /> Consultations
            </Link>
          </div>
        </div>
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
          <Button variant="secondary" style={{ marginLeft: 'auto', fontSize: '0.75rem' }} onClick={loadDoctorDashboard}>
            Retry
          </Button>
        </div>
      )}

      {/* Verification Notice if Pending */}
      {profile?.approval_status === 'PENDING' && (
        <div
          style={{
            background: '#fffbeb',
            border: '1px solid #fde68a',
            color: '#92400e',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <AlertTriangle size={24} color="#b45309" />
          <div style={{ fontSize: '0.875rem' }}>
            <strong>Account Verification In Progress:</strong> Your medical credentials are being reviewed by administrators. Patients can book slots once verified.
          </div>
        </div>
      )}

      {/* Metrics Row (5 Real Operational Stats) */}
      <div className="grid grid-cols-5 gap-4" style={{ marginBottom: '2rem' }}>
        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.625rem', borderRadius: '10px' }}>
              <Clock size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)', fontWeight: 600, textTransform: 'uppercase' }}>Today</div>
              <div style={{ fontSize: '1.375rem', fontWeight: 800 }}>{stats.today_appointments}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ background: '#fef3c7', color: '#b45309', padding: '0.625rem', borderRadius: '10px' }}>
              <Calendar size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)', fontWeight: 600, textTransform: 'uppercase' }}>Upcoming</div>
              <div style={{ fontSize: '1.375rem', fontWeight: 800 }}>{stats.upcoming_appointments}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ background: '#dcfce7', color: '#15803d', padding: '0.625rem', borderRadius: '10px' }}>
              <CheckCircle size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)', fontWeight: 600, textTransform: 'uppercase' }}>Concluded</div>
              <div style={{ fontSize: '1.375rem', fontWeight: 800 }}>{stats.completed_consultations}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ background: 'var(--primary-100)', color: 'var(--primary-700)', padding: '0.625rem', borderRadius: '10px' }}>
              <Users size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)', fontWeight: 600, textTransform: 'uppercase' }}>Patients Treated</div>
              <div style={{ fontSize: '1.375rem', fontWeight: 800 }}>{stats.total_patients}</div>
            </div>
          </div>
        </Card>

        <Card hover>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
            <div style={{ background: '#f1f5f9', color: '#475569', padding: '0.625rem', borderRadius: '10px' }}>
              <FileText size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)', fontWeight: 600, textTransform: 'uppercase' }}>Rx Issued</div>
              <div style={{ fontSize: '1.375rem', fontWeight: 800 }}>{stats.prescriptions_issued}</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Row: Today's Schedule & Pending Actions */}
      <div className="grid grid-cols-2 gap-6" style={{ marginBottom: '2rem' }}>
        {/* Today's Schedule Card */}
        <Card
          title="Today's Consultation Schedule"
          subtitle="Real-time timeline of patients scheduled for today"
          headerAction={
            <Link to="/doctor/appointments" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--primary-600)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
              Calendar <ArrowRight size={14} />
            </Link>
          }
        >
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
              Loading today's schedule...
            </div>
          ) : todaySchedule.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2.5rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
              <Clock size={32} color="var(--primary-600)" style={{ marginBottom: '0.5rem' }} />
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', marginBottom: '0.25rem' }}>No Consultations Scheduled For Today</div>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
                Your schedule for today is open. Review upcoming appointments or configure working hours.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {todaySchedule.map((app) => (
                <div
                  key={app.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem 1rem',
                    background: app.is_past ? '#f8fafc' : '#ffffff',
                    border: '1px solid var(--secondary-200)',
                    borderRadius: '8px',
                    opacity: app.is_past ? 0.75 : 1,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                      {app.patient_name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <Clock size={12} color="var(--primary-600)" />
                      {formatDateTime(app.scheduled_start)} • {app.reason || 'General Consultation'}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {getStatusBadge(app.status)}
                    <Link
                      to="/doctor/appointments"
                      className="btn btn-secondary"
                      style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                    >
                      Manage
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Operational Pending Actions & Availability Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Pending Actions Summary */}
          <Card title="Pending Clinical Actions" subtitle="Actionable items requiring physician review">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px' }}>
                <div>
                  <strong style={{ fontSize: '0.875rem', color: '#92400e' }}>Incoming Booking Requests</strong>
                  <div style={{ fontSize: '0.75rem', color: '#b45309' }}>Patients awaiting slot confirmation</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Badge variant={pendingActions.pending_appointment_requests > 0 ? 'amber' : 'slate'}>
                    {pendingActions.pending_appointment_requests} Pending
                  </Badge>
                  <Link to="/doctor/appointments" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}>
                    Review
                  </Link>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px' }}>
                <div>
                  <strong style={{ fontSize: '0.875rem', color: '#166534' }}>Concluded Visits Awaiting Rx</strong>
                  <div style={{ fontSize: '0.75rem', color: '#15803d' }}>Completed consultations eligible for e-prescription</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Badge variant={pendingActions.completed_awaiting_prescription > 0 ? 'green' : 'slate'}>
                    {pendingActions.completed_awaiting_prescription} Awaiting
                  </Badge>
                  <Link to="/doctor/prescriptions" className="btn btn-primary" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}>
                    Author Rx
                  </Link>
                </div>
              </div>
            </div>
          </Card>

          {/* Schedule & Availability Summary */}
          <Card
            title="Availability & Working Hours"
            subtitle="Weekly appointment slot rules & leave schedule"
            headerAction={
              <Link to="/doctor/availability" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--primary-600)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Edit Schedule <ChevronRight size={14} />
              </Link>
            }
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.8125rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--secondary-100)' }}>
                <span style={{ color: 'var(--secondary-600)' }}>Active Schedule Status:</span>
                <strong>{availability?.has_active_schedule ? `Active (${availability.active_days_count} days/week)` : 'Not Configured'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--secondary-100)' }}>
                <span style={{ color: 'var(--secondary-600)' }}>Slot Duration:</span>
                <strong>{availability?.slot_duration_minutes ? `${availability.slot_duration_minutes} minutes / consultation` : 'Standard (30 mins)'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0' }}>
                <span style={{ color: 'var(--secondary-600)' }}>Next Leave / Holiday:</span>
                <strong>
                  {availability?.next_unavailable_date
                    ? `${formatDate(availability.next_unavailable_date)} (${availability.next_unavailable_reason || 'Off'})`
                    : 'None scheduled'}
                </strong>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* AI Drug Safety Interactive Sandbox */}
      <div className="grid grid-cols-2 gap-6" style={{ marginBottom: '2rem' }}>
        <Card title="Live AI Prescription Interaction Sandbox" subtitle="Test multi-drug, food, and allergy safety algorithms in real-time">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Medications (comma-separated)</label>
              <input
                type="text"
                className="form-input"
                value={testMeds}
                onChange={(e) => setTestMeds(e.target.value)}
                placeholder="e.g. Aspirin, Warfarin, Ciprofloxacin"
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Patient Allergies (comma-separated)</label>
              <input
                type="text"
                className="form-input"
                value={testAllergies}
                onChange={(e) => setTestAllergies(e.target.value)}
                placeholder="e.g. Penicillin, Aspirin"
              />
            </div>

            <Button
              variant="primary"
              onClick={handleRunAiCheck}
              disabled={aiLoading}
              icon={Sparkles}
              style={{ marginTop: '0.5rem' }}
            >
              {aiLoading ? 'Analyzing Clinical Hazards...' : 'Execute AI Safety Analysis'}
            </Button>
          </div>
        </Card>

        {/* AI Safety Output Report */}
        <Card title="AI Safety Output Report" subtitle="Structured clinical reasoning breakdown" className="glass-panel">
          {aiResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Calculated Risk:</span>
                <Badge variant={aiResult.overall_risk_level === 'HIGH' || aiResult.overall_risk_level === 'CRITICAL' ? 'rose' : 'amber'}>
                  {aiResult.overall_risk_level} RISK
                </Badge>
              </div>

              <div style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--secondary-200)', fontSize: '0.8125rem' }}>
                <strong>Summary:</strong> {aiResult.clinical_summary}
              </div>

              {aiResult.drug_drug_interactions?.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-rose)' }}>DRUG-DRUG HAZARDS:</span>
                  {aiResult.drug_drug_interactions.map((d, i) => (
                    <div key={i} style={{ fontSize: '0.8125rem', marginTop: '4px', color: 'var(--secondary-700)' }}>
                      • <strong>{d.entities.join(' + ')}:</strong> {d.description}
                    </div>
                  ))}
                </div>
              )}

              {aiResult.drug_food_interactions?.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-amber)' }}>DRUG-FOOD RESTRICTIONS:</span>
                  {aiResult.drug_food_interactions.map((f, i) => (
                    <div key={i} style={{ fontSize: '0.8125rem', marginTop: '4px', color: 'var(--secondary-700)' }}>
                      • <strong>{f.entities.join(' + ')}:</strong> {f.description}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--secondary-500)', fontSize: '0.875rem' }}>
              Click <strong>"Execute AI Safety Analysis"</strong> to test the prescription evaluation engine.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

export default DoctorDashboardPage;
