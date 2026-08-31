import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Pill,
  Activity,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowLeft,
  RefreshCw,
  User,
  Stethoscope,
  FileText,
  ShieldCheck,
  ShieldAlert,
  Send,
  AlertCircle,
  Sparkles,
  Check,
  PackageCheck,
  X,
  Info,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import pharmacyService from '../../services/pharmacyService';

export function PharmacyPrescriptionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [prescription, setPrescription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Actions
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Modal for status changes / notes
  const [activeModal, setActiveModal] = useState(null); // 'STATUS_CHANGE' | 'DISPENSE'
  const [targetStatus, setTargetStatus] = useState('UNDER_REVIEW');
  const [pharmacyNotes, setPharmacyNotes] = useState('');

  const loadPrescription = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await pharmacyService.getPrescription(id);
      setPrescription(res);
      if (res.pharmacy_notes) {
        setPharmacyNotes(res.pharmacy_notes);
      }
    } catch (err) {
      setError(err.message || `Failed to load prescription #${id}.`);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadPrescription();
  }, [loadPrescription]);

  // Status transition handlers
  const handleOpenStatusModal = (status) => {
    setTargetStatus(status);
    setActionError(null);
    setActiveModal('STATUS_CHANGE');
  };

  const handleOpenDispenseModal = () => {
    setActionError(null);
    setActiveModal('DISPENSE');
  };

  const handleSubmitStatusChange = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      setActionError(null);
      await pharmacyService.updateStatus(prescription.id, {
        status: targetStatus,
        pharmacy_notes: pharmacyNotes,
      });
      setActionSuccess(`Prescription status transitioned to ${targetStatus}.`);
      setActiveModal(null);
      await loadPrescription();
    } catch (err) {
      setActionError(err.message || 'Failed to update prescription status.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitDispense = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      setActionError(null);
      await pharmacyService.dispense(prescription.id, {
        pharmacy_notes: pharmacyNotes,
      });
      setActionSuccess('Prescription successfully dispensed to patient. Real-time notification dispatched.');
      setActiveModal(null);
      await loadPrescription();
    } catch (err) {
      setActionError(err.message || 'Failed to dispense medication.');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PRESCRIBED':
        return <Badge variant="amber">Prescribed (Pending)</Badge>;
      case 'UNDER_REVIEW':
        return <Badge variant="blue">Under Review</Badge>;
      case 'READY':
        return <Badge variant="teal">Ready for Pickup</Badge>;
      case 'DISPENSED':
        return <Badge variant="green">Dispensed</Badge>;
      case 'CANCELLED':
        return <Badge variant="rose">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'CRITICAL':
        return <Badge variant="rose">CRITICAL RISK</Badge>;
      case 'HIGH':
        return <Badge variant="rose">HIGH RISK</Badge>;
      case 'MODERATE':
        return <Badge variant="amber">MODERATE RISK</Badge>;
      case 'LOW':
        return <Badge variant="teal">LOW RISK</Badge>;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
        <Activity size={32} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#0d9488' }} />
        <div>Loading Prescription Dispensary Record...</div>
      </div>
    );
  }

  if (error || !prescription) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Link to="/pharmacy/prescriptions" style={{ color: 'var(--secondary-500)', textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
          <ArrowLeft size={16} style={{ marginRight: '0.25rem' }} /> Back to Queue
        </Link>
        <Card style={{ padding: '2rem', background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c' }}>
          <AlertTriangle size={24} style={{ marginBottom: '0.5rem' }} />
          <div style={{ fontWeight: 700 }}>{error || 'Prescription not found'}</div>
        </Card>
      </div>
    );
  }

  const patientName = prescription.patient?.user?.full_name || `Patient #${prescription.patient_id}`;
  const doctorName = prescription.doctor?.user?.full_name || `Dr. #${prescription.doctor_id}`;
  const aiReport = prescription.latest_ai_report;

  const steps = [
    { label: 'Prescribed by Physician', completed: true },
    {
      label: 'Pharmacist Review',
      completed: ['UNDER_REVIEW', 'READY', 'DISPENSED'].includes(prescription.status),
    },
    {
      label: 'Ready for Patient Pickup',
      completed: ['READY', 'DISPENSED'].includes(prescription.status),
    },
    {
      label: 'Dispensed & Verified',
      completed: prescription.status === 'DISPENSED',
    },
  ];

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Link to="/pharmacy/prescriptions" style={{ color: 'var(--secondary-500)', textDecoration: 'none', display: 'flex', alignItems: 'center', fontSize: '0.875rem' }}>
            <ArrowLeft size={16} style={{ marginRight: '0.25rem' }} /> Prescriptions Queue
          </Link>
          <span style={{ color: 'var(--secondary-300)' }}>/</span>
          <span style={{ fontWeight: 700, color: 'var(--secondary-900)' }}>Prescription #{prescription.id}</span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={loadPrescription}
            disabled={actionLoading}
            style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
          >
            <RefreshCw size={14} className={actionLoading ? 'animate-spin' : ''} /> Refresh
          </Button>
        </div>
      </div>

      {/* Patient & Doctor Context Header */}
      <Card
        className="glass-panel"
        style={{
          padding: '1.5rem',
          background: 'linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%)',
          border: '1px solid #99f6e4',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                Prescription #{prescription.id}
              </span>
              {getStatusBadge(prescription.status)}
              {aiReport && getRiskBadge(aiReport.overall_risk_level)}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', marginTop: '1rem' }}>
              {/* Patient Demographics */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{ background: '#ccfbf1', padding: '0.5rem', borderRadius: '8px', color: '#0f766e' }}>
                  <User size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Patient</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>{patientName}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                    Blood: {prescription.patient?.blood_group || 'N/A'} • Gender: {prescription.patient?.gender || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Prescribing Doctor */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{ background: '#ccfbf1', padding: '0.5rem', borderRadius: '8px', color: '#0f766e' }}>
                  <Stethoscope size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Prescribing Physician</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--secondary-900)' }}>{doctorName}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                    {prescription.doctor?.specialization || 'Physician'}
                  </div>
                </div>
              </div>

              {/* Validity Period */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <div style={{ background: '#ccfbf1', padding: '0.5rem', borderRadius: '8px', color: '#0f766e' }}>
                  <Clock size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', fontWeight: 600 }}>Validity Period</div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--secondary-800)' }}>
                    Valid until {prescription.valid_until ? new Date(prescription.valid_until).toLocaleDateString() : 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>
                    Issued: {new Date(prescription.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Diagnosis & Clinical Notes */}
            <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ padding: '0.75rem 1rem', background: '#ffffff', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.8125rem' }}>
                <strong style={{ color: 'var(--secondary-800)' }}>Clinical Diagnosis:</strong> {prescription.diagnosis}
                {prescription.clinical_notes && (
                  <div style={{ marginTop: '0.25rem', color: 'var(--secondary-600)' }}>
                    <strong>Doctor Instructions:</strong> {prescription.clinical_notes}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Workflow Stepper */}
      <Card className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
          Dispensary Fulfillment Pipeline
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
          {steps.map((step, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                color: step.completed ? '#059669' : 'var(--secondary-400)',
              }}
            >
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: step.completed ? '#d1fae5' : 'var(--secondary-100)',
                  color: step.completed ? '#059669' : 'var(--secondary-400)',
                  fontSize: '0.6875rem',
                }}
              >
                {step.completed ? <Check size={12} /> : idx + 1}
              </div>
              <span>{step.label}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Action Messages */}
      {actionError && (
        <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '0.875rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
          <AlertCircle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {actionError}
        </div>
      )}

      {actionSuccess && (
        <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#047857', padding: '0.875rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
          <CheckCircle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {actionSuccess}
        </div>
      )}

      {/* SECTION 1: AI CLINICAL PHARMACOTHERAPY SAFETY REPORT */}
      {aiReport && (
        <Card
          className="glass-panel"
          style={{
            padding: '1.5rem',
            border: `1px solid ${aiReport.overall_risk_level === 'HIGH' || aiReport.overall_risk_level === 'CRITICAL' ? '#fecdd3' : '#e2e8f0'}`,
            background: aiReport.overall_risk_level === 'HIGH' || aiReport.overall_risk_level === 'CRITICAL' ? '#fff5f5' : '#ffffff',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ background: '#ede9fe', padding: '0.5rem', borderRadius: '8px', color: '#7c3aed' }}>
                <Sparkles size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--secondary-900)' }}>
                  CareAI Pharmacotherapy Safety Assessment
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                  Automated drug-drug, food-drug, and patient allergy contraindication audit
                </span>
              </div>
            </div>

            {getRiskBadge(aiReport.overall_risk_level)}
          </div>

          {/* Clinical Summary & Recommendations */}
          {aiReport.clinical_summary && (
            <div style={{ padding: '0.875rem 1rem', background: 'rgba(255, 255, 255, 0.85)', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', marginBottom: '1rem', fontSize: '0.875rem' }}>
              <strong style={{ color: 'var(--secondary-800)' }}>Clinical Summary:</strong> {aiReport.clinical_summary}
            </div>
          )}

          {/* Findings List */}
          {(aiReport.findings || []).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
              {aiReport.findings.map((finding, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '0.875rem 1rem',
                    background: '#ffffff',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--secondary-200)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.375rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--secondary-900)' }}>
                      {finding.title || `${finding.category} Interaction`}
                    </span>
                    <Badge variant={finding.severity === 'HIGH' || finding.severity === 'CRITICAL' ? 'rose' : 'amber'}>
                      {finding.severity}
                    </Badge>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-700)' }}>
                    {finding.explanation}
                  </div>
                  {finding.recommended_action && (
                    <div style={{ fontSize: '0.75rem', color: '#0d9488', fontWeight: 600 }}>
                      Action: {finding.recommended_action}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '1rem', background: '#ecfdf5', borderRadius: 'var(--radius-md)', color: '#065f46', fontSize: '0.8125rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={16} /> No hazardous drug-drug or allergy contraindications detected for this medication regimen.
            </div>
          )}

          {/* Mandatory AI Safety Disclaimer */}
          <div
            style={{
              padding: '0.75rem 1rem',
              background: '#f8fafc',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #e2e8f0',
              fontSize: '0.75rem',
              color: 'var(--secondary-500)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <Info size={16} style={{ flexShrink: 0, color: 'var(--secondary-400)' }} />
            <span>
              <strong>Disclaimer:</strong> {aiReport.disclaimer || 'AI safety insights are informational decision-support tools and do not replace professional clinical judgment.'}
            </span>
          </div>
        </Card>
      )}

      {/* SECTION 2: IMMUTABLE DOCTOR PRESCRIBED MEDICATIONS */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Pill size={20} color="#0d9488" /> Prescribed Medications & Instructions
            </h3>
            <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
              Physician prescription items (Legally immutable clinical record)
            </span>
          </div>
          <Badge variant="secondary">Doctor Prescribed</Badge>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'var(--secondary-50)', borderBottom: '1px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Medication Name</th>
                <th style={{ padding: '0.75rem 1rem' }}>Dosage</th>
                <th style={{ padding: '0.75rem 1rem' }}>Frequency</th>
                <th style={{ padding: '0.75rem 1rem' }}>Duration</th>
                <th style={{ padding: '0.75rem 1rem' }}>Route</th>
                <th style={{ padding: '0.75rem 1rem' }}>Special Instructions</th>
              </tr>
            </thead>
            <tbody>
              {(prescription.items || []).map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                  <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                    {item.medication_name || item.drug_name}
                  </td>
                  <td style={{ padding: '0.875rem 1rem', fontWeight: 600 }}>{item.dosage}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>{item.frequency}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>{item.duration}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>{item.route_of_administration || 'Oral'}</td>
                  <td style={{ padding: '0.875rem 1rem', color: 'var(--secondary-600)' }}>
                    {item.instructions || 'As directed by physician'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* SECTION 3: PHARMACIST WORKFLOW & DISPENSATION CONTROLS */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <PackageCheck size={20} color="#0d9488" /> Pharmacist Dispensary Actions
            </h3>
            <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
              Manage review stages, verify patient ID, add pharmacy fulfillment notes, and record dispensing.
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {prescription.status === 'PRESCRIBED' && (
              <Button
                variant="primary"
                onClick={() => handleOpenStatusModal('UNDER_REVIEW')}
                disabled={actionLoading}
                style={{ background: '#0284c7', borderColor: '#0284c7' }}
              >
                Mark Under Review
              </Button>
            )}

            {(prescription.status === 'PRESCRIBED' || prescription.status === 'UNDER_REVIEW') && (
              <Button
                variant="primary"
                onClick={() => handleOpenStatusModal('READY')}
                disabled={actionLoading}
                style={{ background: '#0d9488', borderColor: '#0d9488' }}
              >
                <CheckCircle size={15} style={{ marginRight: '0.25rem' }} /> Mark Ready for Pickup
              </Button>
            )}

            {prescription.status !== 'DISPENSED' && prescription.status !== 'CANCELLED' && (
              <Button
                variant="primary"
                onClick={handleOpenDispenseModal}
                disabled={actionLoading}
                style={{ background: '#059669', borderColor: '#059669' }}
              >
                <PackageCheck size={16} style={{ marginRight: '0.25rem' }} /> Dispense Medication
              </Button>
            )}
          </div>
        </div>

        {/* Pharmacy Notes Display */}
        {prescription.pharmacy_notes && (
          <div style={{ padding: '0.875rem 1rem', background: 'var(--bg-main)', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <strong style={{ color: 'var(--secondary-800)' }}>Pharmacist Notes:</strong> {prescription.pharmacy_notes}
          </div>
        )}

        {/* Dispensed Audit Information */}
        {prescription.status === 'DISPENSED' && (
          <div style={{ padding: '1rem', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 'var(--radius-md)', color: '#065f46', fontSize: '0.875rem' }}>
            <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle size={18} /> Medication Dispensed
            </div>
            <div style={{ marginTop: '0.375rem', fontSize: '0.8125rem' }}>
              Dispensed by: <strong>{prescription.dispensed_by_name || 'Pharmacist'}</strong> • Timestamp:{' '}
              {prescription.dispensed_at ? new Date(prescription.dispensed_at).toLocaleString() : 'N/A'}
            </div>
          </div>
        )}
      </Card>

      {/* Modal: Status Change */}
      {activeModal === 'STATUS_CHANGE' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '500px', width: '100%', padding: '1.75rem', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                Update Fulfillment Status: {targetStatus}
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmitStatusChange} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Pharmacist Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  value={pharmacyNotes}
                  onChange={(e) => setPharmacyNotes(e.target.value)}
                  placeholder="e.g. Packaged into staging bin #4. Drug interactions verified with patient history."
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="ghost" type="button" onClick={() => setActiveModal(null)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={actionLoading} style={{ background: '#0d9488' }}>
                  {actionLoading ? 'Updating...' : 'Confirm Status Update'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Dispense Confirmation */}
      {activeModal === 'DISPENSE' && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '520px', width: '100%', padding: '1.75rem', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <PackageCheck size={20} color="#059669" /> Confirm Dispensation
              </h3>
              <button type="button" onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmitDispense} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ fontSize: '0.875rem', color: 'var(--secondary-700)', lineHeight: 1.5 }}>
                You are recording the final physical dispensation of medications for <strong>{patientName}</strong>. This will record your pharmacist signature and timestamp.
              </div>

              <div>
                <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-700)', display: 'block', marginBottom: '0.25rem' }}>
                  Dispensing Notes & Patient Counseling Record
                </label>
                <textarea
                  rows={3}
                  value={pharmacyNotes}
                  onChange={(e) => setPharmacyNotes(e.target.value)}
                  placeholder="e.g. Verified patient ID, counseled on dosage schedule with meals."
                  style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--secondary-200)', fontSize: '0.875rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <Button variant="ghost" type="button" onClick={() => setActiveModal(null)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={actionLoading} style={{ background: '#059669' }}>
                  {actionLoading ? 'Dispensing...' : 'Confirm Dispense'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default PharmacyPrescriptionDetailPage;
