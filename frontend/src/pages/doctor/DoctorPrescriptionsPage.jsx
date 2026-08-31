import React, { useState, useEffect } from 'react';
import {
  FileText,
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Calendar,
  User,
  Clock,
  Pill,
  Send,
  Sparkles,
  Eye,
  X,
  Stethoscope,
  Activity,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import appointmentService from '../../services/appointmentService';
import prescriptionService from '../../services/prescriptionService';
import aiService from '../../services/aiService';
import AISafetyReportModal from '../../components/ai/AISafetyReportModal';
import { formatDateTime, formatDate, formatAllergiesDisplay, formatConditionsDisplay } from '../../utils/formatters';

const DEFAULT_MEDICATION_ROW = {
  medication_name: '',
  dosage: '',
  frequency: 'Twice daily',
  duration: '5 days',
  route_of_administration: 'Oral',
  instructions: 'Take after food',
};

export function DoctorPrescriptionsPage() {
  const [completedAppointments, setCompletedAppointments] = useState([]);
  const [issuedPrescriptions, setIssuedPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);

  // Form State
  const [selectedAppointmentId, setSelectedAppointmentId] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [validUntil, setValidUntil] = useState('');
  const [medications, setMedications] = useState([{ ...DEFAULT_MEDICATION_ROW }]);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  // View Details Modal
  const [viewingPrescription, setViewingPrescription] = useState(null);

  // AI Safety Analysis State
  const [activeSafetyReport, setActiveSafetyReport] = useState(null);
  const [analyzingDraft, setAnalyzingDraft] = useState(false);
  const [analyzingRxId, setAnalyzingRxId] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [appData, rxData] = await Promise.all([
        appointmentService.getMyDoctorAppointments('COMPLETED').catch(() => []),
        prescriptionService.getMyDoctorPrescriptions().catch(() => []),
      ]);
      setCompletedAppointments(appData || []);
      setIssuedPrescriptions(rxData || []);

      const prescribedAppointmentIds = new Set((rxData || []).map((r) => r.appointment_id));
      const unprescribed = (appData || []).filter((a) => !prescribedAppointmentIds.has(a.id));
      if (unprescribed.length > 0 && !selectedAppointmentId) {
        setSelectedAppointmentId(String(unprescribed[0].id));
        setDiagnosis(unprescribed[0].reason || '');
        setClinicalNotes(unprescribed[0].doctor_notes || '');
      }
    } catch (err) {
      console.error('Failed to load prescription data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAppointmentSelect = (appId) => {
    setSelectedAppointmentId(appId);
    setFormError(null);
    const app = completedAppointments.find((a) => String(a.id) === String(appId));
    if (app) {
      setDiagnosis(app.reason || '');
      setClinicalNotes(app.doctor_notes || '');
    }
  };

  const handleAddMedicationRow = () => {
    setMedications([...medications, { ...DEFAULT_MEDICATION_ROW }]);
  };

  const handleRemoveMedicationRow = (index) => {
    if (medications.length <= 1) return;
    const updated = medications.filter((_, i) => i !== index);
    setMedications(updated);
  };

  const handleMedicationChange = (index, field, value) => {
    const updated = [...medications];
    updated[index][field] = value;
    setMedications(updated);
  };

  const handleRunDraftSafetyCheck = async () => {
    const validMeds = medications
      .map((m) => m.medication_name.trim())
      .filter((name) => name.length > 0);

    if (validMeds.length === 0) {
      setFormError('Please enter at least one medication name to run pre-flight safety analysis.');
      return;
    }

    try {
      setAnalyzingDraft(true);
      setFormError(null);
      const rawAllergies = app?.patient?.allergies;
      const allergies = Array.isArray(rawAllergies)
        ? rawAllergies.map((a) => (typeof a === 'object' && a !== null ? a.name : String(a))).filter(Boolean)
        : typeof rawAllergies === 'string'
        ? rawAllergies.split(',').map((a) => a.trim()).filter(Boolean)
        : [];

      const rawConditions = app?.patient?.chronic_conditions;
      const conditions = Array.isArray(rawConditions)
        ? rawConditions.map((c) => (typeof c === 'object' && c !== null ? c.name || c.condition : String(c))).filter(Boolean)
        : typeof rawConditions === 'string'
        ? rawConditions.split(',').map((c) => c.trim()).filter(Boolean)
        : [];

      const report = await aiService.analyzeInteractions({
        medications: validMeds,
        patient_allergies: allergies,
        patient_conditions: conditions,
      });
      setActiveSafetyReport(report);
    } catch (err) {
      console.error('Draft AI safety check failed:', err);
      setFormError(err.message || 'Pre-flight safety check failed.');
    } finally {
      setAnalyzingDraft(false);
    }
  };

  const handleRunPrescriptionSafetyCheck = async (prescription) => {
    try {
      setAnalyzingRxId(prescription.id);
      const report = await aiService.analyzePrescription(prescription.id);
      setActiveSafetyReport(report);
    } catch (err) {
      console.error('Prescription AI safety check failed:', err);
      setActionMessage(err.message || 'Failed to analyze prescription safety.');
    } finally {
      setAnalyzingRxId(null);
    }
  };

  const handlePrescriptionSubmit = async (e) => {
    e.preventDefault();
    if (!selectedAppointmentId) {
      setFormError('Please select a completed appointment.');
      return;
    }
    if (!diagnosis.trim()) {
      setFormError('Please enter a clinical diagnosis or summary.');
      return;
    }

    for (let i = 0; i < medications.length; i++) {
      const med = medications[i];
      if (!med.medication_name.trim()) {
        setFormError(`Medication #${i + 1} must have a valid medication name.`);
        return;
      }
      if (!med.dosage.trim()) {
        setFormError(`Please enter dosage for ${med.medication_name || `Medication #${i + 1}`}.`);
        return;
      }
      if (!med.frequency.trim()) {
        setFormError(`Please enter frequency for ${med.medication_name || `Medication #${i + 1}`}.`);
        return;
      }
      if (!med.duration.trim()) {
        setFormError(`Please enter duration for ${med.medication_name || `Medication #${i + 1}`}.`);
        return;
      }
    }

    try {
      setSubmitting(true);
      setFormError(null);

      const payload = {
        appointment_id: Number(selectedAppointmentId),
        diagnosis: diagnosis.trim(),
        clinical_notes: clinicalNotes.trim() || undefined,
        valid_until: validUntil || undefined,
        items: medications.map((m) => ({
          medication_name: m.medication_name.trim(),
          dosage: m.dosage.trim(),
          frequency: m.frequency.trim(),
          duration: m.duration.trim(),
          route_of_administration: m.route_of_administration || 'Oral',
          instructions: m.instructions.trim() || undefined,
        })),
      };

      const created = await prescriptionService.createPrescription(payload);
      setActionMessage(`Digital prescription #${created.id} successfully issued!`);

      // Reset form
      setDiagnosis('');
      setClinicalNotes('');
      setValidUntil('');
      setMedications([{ ...DEFAULT_MEDICATION_ROW }]);
      loadData();
    } catch (err) {
      console.error('Failed to create prescription:', err);
      setFormError(err.message || 'Failed to issue prescription.');
    } finally {
      setSubmitting(false);
    }
  };

  const prescribedAppointmentIds = new Set(issuedPrescriptions.map((r) => r.appointment_id));
  const pendingPrescriptionApps = completedAppointments.filter((a) => !prescribedAppointmentIds.has(a.id));
  const selectedApp = completedAppointments.find((a) => String(a.id) === String(selectedAppointmentId));

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
          <FileText size={28} color="var(--primary-700)" />
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>Clinical Prescription Authoring Studio</h1>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Author structured digital prescriptions with AI-assisted pre-flight interaction checking, allergy contraindication audits, and dosage scheduling.
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

      {/* Two-Column Grid: Authoring Form & Eligible Consultations */}
      <div className="grid grid-cols-3 gap-6" style={{ marginBottom: '2.5rem' }}>
        {/* Left Column: Eligible Completed Appointments (1 col) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Card
            title="Concluded Consultations"
            subtitle={`${pendingPrescriptionApps.length} awaiting prescription`}
          >
            {loading ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
                Loading consultations...
              </div>
            ) : pendingPrescriptionApps.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '1.5rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--secondary-200)' }}>
                <CheckCircle size={28} color="var(--primary-600)" style={{ marginBottom: '0.5rem' }} />
                <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>All Completed Visits Prescribed</div>
                <p style={{ color: 'var(--secondary-500)', fontSize: '0.75rem', marginTop: '4px' }}>
                  No pending completed visits requiring prescription.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                {pendingPrescriptionApps.map((app) => (
                  <div
                    key={app.id}
                    onClick={() => handleAppointmentSelect(app.id)}
                    style={{
                      padding: '0.75rem',
                      borderRadius: 'var(--radius-md)',
                      border: String(selectedAppointmentId) === String(app.id) ? '2px solid var(--primary-600)' : '1px solid var(--secondary-200)',
                      background: String(selectedAppointmentId) === String(app.id) ? 'var(--primary-50)' : '#ffffff',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                        {app.patient?.user?.full_name || `Patient #${app.patient_id}`}
                      </span>
                      <Badge variant="teal" style={{ fontSize: '0.6875rem' }}>Completed</Badge>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} color="var(--primary-600)" />
                      {formatDateTime(app.scheduled_start)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-700)', marginTop: '4px' }}>
                      <strong>Reason:</strong> {app.reason || app.reason_for_visit}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Digital Prescription Form (2 cols) */}
        <div style={{ gridColumn: 'span 2' }}>
          <Card
            title="Digital Prescription Authoring Workspace"
            subtitle="Author verified e-prescriptions with multi-drug scheduling & pre-flight AI check"
            className="glass-panel"
          >
            {formError && (
              <div
                style={{
                  background: '#fff1f2',
                  border: '1px solid #fecdd3',
                  color: '#9f1239',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '1.25rem',
                  fontSize: '0.8125rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <AlertCircle size={16} />
                <span>{formError}</span>
              </div>
            )}

            {/* Selected Patient Banner */}
            {selectedApp && (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: '#f8fafc',
                  border: '1px solid var(--secondary-200)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.75rem 1rem',
                  marginBottom: '1.25rem',
                  fontSize: '0.8125rem',
                }}
              >
                <div>
                  <span style={{ color: 'var(--secondary-500)' }}>Target Patient:</span>{' '}
                  <strong>{selectedApp.patient?.user?.full_name || `Patient #${selectedApp.patient_id}`}</strong>
                  <span style={{ color: 'var(--secondary-400)', margin: '0 6px' }}>•</span>
                  <span>Blood: {selectedApp.patient?.blood_group || 'O+'}</span>
                  <span style={{ color: 'var(--secondary-400)', margin: '0 6px' }}>•</span>
                  <span style={{ color: selectedApp.patient?.allergies?.length ? 'var(--accent-rose)' : 'var(--secondary-500)', fontWeight: selectedApp.patient?.allergies?.length ? 700 : 400 }}>
                    Allergies: {formatAllergiesDisplay(selectedApp.patient?.allergies)}
                  </span>
                </div>
                <Badge variant="blue">Appointment #{selectedApp.id}</Badge>
              </div>
            )}

            <form onSubmit={handlePrescriptionSubmit}>
              {/* Diagnosis and Notes */}
              <div className="grid grid-cols-2 gap-4" style={{ marginBottom: '1rem' }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Clinical Diagnosis / Summary *</label>
                  <input
                    type="text"
                    className="form-input"
                    required
                    placeholder="e.g. Acute Bacterial Pharyngitis, Type 2 Diabetes"
                    value={diagnosis}
                    onChange={(e) => setDiagnosis(e.target.value)}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Valid Until (Optional)</label>
                  <input
                    type="date"
                    className="form-input"
                    min={new Date().toISOString().split('T')[0]}
                    value={validUntil}
                    onChange={(e) => setValidUntil(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                <label className="form-label">Clinical Notes / General Instructions</label>
                <textarea
                  className="form-input"
                  rows={2}
                  placeholder="e.g. Complete the entire antibiotic course. Hydrate adequately and avoid direct sun exposure while on treatment."
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                />
              </div>

              {/* Dynamic Medication Items Section */}
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Pill size={18} color="var(--primary-700)" />
                    <h4 style={{ fontSize: '0.9375rem', fontWeight: 700 }}>Prescribed Medications ({medications.length})</h4>
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    icon={Plus}
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                    onClick={handleAddMedicationRow}
                  >
                    Add Medication
                  </Button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {medications.map((med, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: '#ffffff',
                        border: '1px solid var(--secondary-200)',
                        borderRadius: 'var(--radius-md)',
                        padding: '1rem',
                        position: 'relative',
                        boxShadow: 'var(--shadow-sm)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary-700)' }}>
                          ITEM #{idx + 1}
                        </span>
                        {medications.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveMedicationRow(idx)}
                            style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer', padding: '2px' }}
                            title="Remove Medication Item"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-3 gap-3" style={{ marginBottom: '0.75rem' }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Medication Name *</label>
                          <input
                            type="text"
                            className="form-input"
                            style={{ fontSize: '0.8125rem', padding: '0.5rem' }}
                            placeholder="e.g. Amoxicillin, Warfarin, Aspirin"
                            value={med.medication_name}
                            onChange={(e) => handleMedicationChange(idx, 'medication_name', e.target.value)}
                            required
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Dosage *</label>
                          <input
                            type="text"
                            className="form-input"
                            style={{ fontSize: '0.8125rem', padding: '0.5rem' }}
                            placeholder="e.g. 500 mg"
                            value={med.dosage}
                            onChange={(e) => handleMedicationChange(idx, 'dosage', e.target.value)}
                            required
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Frequency *</label>
                          <input
                            type="text"
                            className="form-input"
                            style={{ fontSize: '0.8125rem', padding: '0.5rem' }}
                            placeholder="e.g. Twice daily"
                            value={med.frequency}
                            onChange={(e) => handleMedicationChange(idx, 'frequency', e.target.value)}
                            required
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Duration *</label>
                          <input
                            type="text"
                            className="form-input"
                            style={{ fontSize: '0.8125rem', padding: '0.5rem' }}
                            placeholder="e.g. 7 days"
                            value={med.duration}
                            onChange={(e) => handleMedicationChange(idx, 'duration', e.target.value)}
                            required
                          />
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Route of Admin</label>
                          <select
                            className="form-input"
                            style={{ fontSize: '0.8125rem', padding: '0.5rem' }}
                            value={med.route_of_administration}
                            onChange={(e) => handleMedicationChange(idx, 'route_of_administration', e.target.value)}
                          >
                            <option value="Oral">Oral (P.O.)</option>
                            <option value="Topical">Topical</option>
                            <option value="Intravenous">Intravenous (I.V.)</option>
                            <option value="Inhalation">Inhalation</option>
                            <option value="Sublingual">Sublingual</option>
                            <option value="Ophthalmic">Ophthalmic (Eye)</option>
                          </select>
                        </div>

                        <div className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Special Instructions</label>
                          <input
                            type="text"
                            className="form-input"
                            style={{ fontSize: '0.8125rem', padding: '0.5rem' }}
                            placeholder="e.g. Take after meals with full glass of water"
                            value={med.instructions}
                            onChange={(e) => handleMedicationChange(idx, 'instructions', e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Form Submission and Pre-Flight Check */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                <Button
                  type="button"
                  variant="secondary"
                  icon={Sparkles}
                  disabled={analyzingDraft}
                  onClick={handleRunDraftSafetyCheck}
                  style={{ padding: '0.5rem 1rem', fontSize: '0.8125rem' }}
                >
                  {analyzingDraft ? 'Checking Safety...' : 'Run Pre-Flight AI Safety Audit'}
                </Button>

                <Button
                  type="submit"
                  variant="primary"
                  icon={Send}
                  disabled={submitting || !selectedAppointmentId}
                  style={{ padding: '0.625rem 1.5rem' }}
                >
                  {submitting ? 'Issuing E-Prescription...' : 'Sign & Issue Digital Prescription'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>

      {/* Previously Issued Prescriptions Log */}
      <Card title="Issued Prescription History" subtitle="Audited digital prescription log authored by your account">
        {issuedPrescriptions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--secondary-500)', fontSize: '0.875rem' }}>
            No prescriptions issued yet. Select a completed consultation above to issue your first e-prescription.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--secondary-200)', color: 'var(--secondary-600)' }}>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Rx ID</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Patient Name</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Diagnosis</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Medications</th>
                  <th style={{ padding: '0.75rem 0.5rem' }}>Date Issued</th>
                  <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {issuedPrescriptions.map((rx) => (
                  <tr key={rx.id} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                    <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700 }}>#RX-{rx.id}</td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>
                      <strong>{rx.patient?.user?.full_name || `Patient #${rx.patient_id}`}</strong>
                    </td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>{rx.diagnosis}</td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {rx.items?.map((item, i) => (
                          <Badge key={i} variant="teal" style={{ fontSize: '0.6875rem' }}>
                            {item.medication_name || item.drug_name} ({item.dosage})
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem 0.5rem' }}>{formatDate(rx.created_at)}</td>
                    <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '0.375rem', justifyContent: 'flex-end' }}>
                        <Button
                          variant="secondary"
                          style={{ padding: '0.3rem 0.625rem', fontSize: '0.75rem' }}
                          icon={Sparkles}
                          disabled={analyzingRxId === rx.id}
                          onClick={() => handleRunPrescriptionSafetyCheck(rx)}
                        >
                          AI Safety
                        </Button>
                        <Button
                          variant="secondary"
                          style={{ padding: '0.3rem 0.625rem', fontSize: '0.75rem' }}
                          icon={Eye}
                          onClick={() => setViewingPrescription(rx)}
                        >
                          Script
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Prescription Detail Modal */}
      {viewingPrescription && (
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
              maxWidth: '650px',
              width: '100%',
              boxShadow: 'var(--shadow-xl)',
              overflow: 'hidden',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '1.25rem 1.5rem',
                borderBottom: '1px solid var(--secondary-200)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'linear-gradient(135deg, var(--primary-50) 0%, #ffffff 100%)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <Stethoscope size={22} color="var(--primary-700)" />
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 800 }}>Digital Prescription #RX-{viewingPrescription.id}</h3>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                    Issued on {formatDate(viewingPrescription.created_at)}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setViewingPrescription(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-400)', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto' }}>
              {/* Clinical Header Details */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '1rem',
                  padding: '1rem',
                  background: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--secondary-200)',
                  marginBottom: '1.25rem',
                  fontSize: '0.8125rem',
                }}
              >
                <div>
                  <div style={{ color: 'var(--secondary-500)' }}>Patient Details</div>
                  <strong style={{ fontSize: '0.9375rem' }}>
                    {viewingPrescription.patient?.user?.full_name || `Patient #${viewingPrescription.patient_id}`}
                  </strong>
                  <div style={{ color: 'var(--secondary-600)', marginTop: '2px' }}>
                    Blood Group: {viewingPrescription.patient?.blood_group || 'O+'} • Allergies: {formatAllergiesDisplay(viewingPrescription.patient?.allergies)}
                  </div>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)' }}>Prescribing Physician</div>
                  <strong style={{ fontSize: '0.9375rem' }}>
                    Dr. {viewingPrescription.doctor?.user?.full_name || 'Practitioner'}
                  </strong>
                  <div style={{ color: 'var(--secondary-600)', marginTop: '2px' }}>
                    {viewingPrescription.doctor?.specialization} • License: {viewingPrescription.doctor?.license_number}
                  </div>
                </div>
              </div>

              {/* Diagnosis */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Clinical Diagnosis
                </div>
                <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                  {viewingPrescription.diagnosis}
                </div>
                {viewingPrescription.clinical_notes && (
                  <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)', marginTop: '4px' }}>
                    {viewingPrescription.clinical_notes}
                  </p>
                )}
              </div>

              {/* Prescribed Items Table */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Prescribed Medications (Rx)
                </div>
                <div style={{ border: '1px solid var(--secondary-200)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'var(--primary-50)', color: 'var(--primary-900)', borderBottom: '1px solid var(--secondary-200)' }}>
                        <th style={{ padding: '0.5rem 0.75rem' }}>Medication</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>Dosage</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>Frequency</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>Duration</th>
                        <th style={{ padding: '0.5rem 0.75rem' }}>Instructions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {viewingPrescription.items?.map((item, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                          <td style={{ padding: '0.5rem 0.75rem', fontWeight: 700 }}>
                            {item.medication_name || item.drug_name}
                            <span style={{ fontSize: '0.6875rem', color: 'var(--secondary-500)', display: 'block', fontWeight: 400 }}>
                              Route: {item.route_of_administration || 'Oral'}
                            </span>
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem' }}>{item.dosage}</td>
                          <td style={{ padding: '0.5rem 0.75rem' }}>{item.frequency}</td>
                          <td style={{ padding: '0.5rem 0.75rem' }}>{item.duration}</td>
                          <td style={{ padding: '0.5rem 0.75rem', color: 'var(--secondary-600)' }}>
                            {item.instructions || 'As directed'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Security Seal */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem',
                  background: 'var(--primary-50)',
                  border: '1px solid var(--primary-200)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                  color: 'var(--primary-800)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Sparkles size={16} />
                  <span>Verified Clinical E-Prescription • CareAI Health Network</span>
                </div>
                <span>Ref: #{viewingPrescription.appointment_id ? `APT-${viewingPrescription.appointment_id}` : 'DIRECT'}</span>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between' }}>
              <Button
                variant="primary"
                icon={Sparkles}
                disabled={analyzingRxId === viewingPrescription.id}
                onClick={() => handleRunPrescriptionSafetyCheck(viewingPrescription)}
              >
                Run AI Safety Audit
              </Button>

              <Button variant="secondary" onClick={() => setViewingPrescription(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* AI Safety Analysis Modal */}
      {activeSafetyReport && (
        <AISafetyReportModal
          report={activeSafetyReport}
          onClose={() => setActiveSafetyReport(null)}
          prescriptionInfo={viewingPrescription}
        />
      )}
    </div>
  );
}

export default DoctorPrescriptionsPage;
