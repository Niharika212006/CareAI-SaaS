import React, { useState } from 'react';
import {
  X,
  FileText,
  Sparkles,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Stethoscope,
  Pill,
} from 'lucide-react';
import FileUploadZone from '../common/FileUploadZone';
import aiAssistantService from '../../services/aiAssistantService';

export default function PrescriptionUploadModal({ isOpen, onClose, onPrescriptionSaved }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState(null);

  // Extracted Draft State
  const [draft, setDraft] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(null);

  if (!isOpen) return null;

  const handleFileSelected = (file) => {
    setSelectedFile(file);
    setExtractError(null);
  };

  const handleStartExtraction = async () => {
    if (!selectedFile) return;
    setIsExtracting(true);
    setExtractError(null);

    try {
      const draftResult = await aiAssistantService.uploadPrescriptionDraft(selectedFile);
      setDraft(draftResult);
    } catch (err) {
      console.error('Prescription extraction failed:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to extract prescription. Please try again.';
      setExtractError(msg);
    } finally {
      setIsExtracting(false);
    }
  };

  // Medication row management in draft
  const handleMedicationChange = (index, field, value) => {
    if (!draft) return;
    const updatedMeds = [...draft.medications];
    updatedMeds[index] = { ...updatedMeds[index], [field]: value };
    setDraft({ ...draft, medications: updatedMeds });
  };

  const handleAddMedication = () => {
    if (!draft) return;
    const newMed = {
      medication_name: '',
      dosage: '1 tablet',
      frequency: 'Once daily',
      duration: '30 days',
      route_of_administration: 'Oral',
      instructions: 'Take with water',
    };
    setDraft({ ...draft, medications: [...draft.medications, newMed] });
  };

  const handleRemoveMedication = (index) => {
    if (!draft) return;
    const updatedMeds = draft.medications.filter((_, i) => i !== index);
    setDraft({ ...draft, medications: updatedMeds });
  };

  const handleConfirmAndSave = async () => {
    if (!draft) return;
    setIsSaving(true);
    setExtractError(null);

    try {
      const payload = {
        temp_file_token: draft.temp_file_token,
        file_name: draft.file_name,
        doctor_name: draft.doctor_name,
        diagnosis: draft.diagnosis || 'Clinical Prescription',
        clinical_notes: draft.clinical_notes,
        medications: draft.medications.filter((m) => m.medication_name.trim().length > 0),
      };

      const result = await aiAssistantService.confirmPrescription(payload);
      setSaveSuccess(result);
      if (onPrescriptionSaved) {
        onPrescriptionSaved(result, draft);
      }
    } catch (err) {
      console.error('Failed to confirm prescription:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to save prescription to records.';
      setExtractError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setDraft(null);
    setSaveSuccess(null);
    setExtractError(null);
  };

  const handleModalClose = () => {
    handleReset();
    onClose();
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.55)',
        backdropFilter: 'blur(5px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.25rem',
      }}
      className="animate-fade-in"
      onClick={handleModalClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '740px',
          maxHeight: '90vh',
          backgroundColor: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          border: '1px solid var(--secondary-200)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--secondary-200)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(135deg, #0d9488 0%, #0284c7 100%)',
            color: '#ffffff',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FileText size={20} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0 }}>
                Upload & Verify Prescription
              </h3>
              <p style={{ fontSize: '0.8125rem', opacity: 0.9, margin: 0 }}>
                CareAI Multimodal Ingestion & Verification
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleModalClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#ffffff',
              cursor: 'pointer',
              padding: '0.375rem',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div
          style={{
            padding: '1.5rem',
            overflowY: 'auto',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: '1.25rem',
          }}
        >
          {extractError && (
            <div
              style={{
                padding: '0.875rem 1rem',
                backgroundColor: 'var(--danger-50)',
                border: '1px solid var(--danger-200)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--danger-800)',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.625rem',
              }}
            >
              <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>{extractError}</div>
            </div>
          )}

          {/* STEP 1: Uploading & Initial Screen */}
          {!draft && !saveSuccess && (
            <div>
              <p style={{ fontSize: '0.875rem', color: 'var(--secondary-600)', marginBottom: '1rem' }}>
                Upload a clear scan or digital copy of your doctor's prescription (PDF, JPG, PNG). CareAI's multimodal clinical vision model will extract medication names, dosages, and instructions for your personal review.
              </p>

              <FileUploadZone
                selectedFile={selectedFile}
                onFileSelected={handleFileSelected}
                onClear={() => setSelectedFile(null)}
                disabled={isExtracting}
              />

              {selectedFile && (
                <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleStartExtraction}
                    disabled={isExtracting}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.75rem 1.5rem',
                      fontWeight: 600,
                    }}
                  >
                    {isExtracting ? (
                      <>
                        <Clock size={16} className="animate-spin" />
                        Extracting Details with CareAI...
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        Analyze & Extract Details
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Extraction Review & Verification */}
          {draft && !saveSuccess && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1rem',
                  backgroundColor: 'var(--primary-50)',
                  border: '1px solid var(--primary-200)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--primary-900)',
                  fontSize: '0.8125rem',
                }}
              >
                <ShieldCheck size={18} color="var(--primary-700)" style={{ flexShrink: 0 }} />
                <span>
                  <strong>Clinical Verification Required:</strong> CareAI extracted these details from your document. Please verify all medications, dosages, and instructions before confirming.
                </span>
              </div>

              {/* Metadata Fields */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '1rem',
                }}
              >
                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-700)', textTransform: 'uppercase' }}>
                    Prescribing Doctor / Clinic
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    value={draft.doctor_name || ''}
                    onChange={(e) => setDraft({ ...draft, doctor_name: e.target.value })}
                    placeholder="e.g. Dr. Sarah Jenkins, MD"
                    style={{ width: '100%', marginTop: '0.25rem', padding: '0.5rem 0.75rem', fontSize: '0.875rem' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-700)', textTransform: 'uppercase' }}>
                    Diagnosis / Condition
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    value={draft.diagnosis || ''}
                    onChange={(e) => setDraft({ ...draft, diagnosis: e.target.value })}
                    placeholder="e.g. Essential Hypertension"
                    style={{ width: '100%', marginTop: '0.25rem', padding: '0.5rem 0.75rem', fontSize: '0.875rem' }}
                  />
                </div>
              </div>

              {/* Medications List Table */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <label style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--secondary-800)' }}>
                    Prescribed Medications ({draft.medications.length})
                  </label>
                  <button
                    type="button"
                    onClick={handleAddMedication}
                    className="btn btn-secondary btn-sm"
                    style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
                  >
                    <Plus size={14} /> Add Drug
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {draft.medications.map((med, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '0.875rem',
                        backgroundColor: 'var(--bg-main)',
                        border: '1px solid var(--secondary-200)',
                        borderRadius: 'var(--radius-md)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.5rem',
                      }}
                    >
                      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                        <div style={{ flex: 2 }}>
                          <input
                            type="text"
                            placeholder="Medication Name (e.g. Lisinopril)"
                            value={med.medication_name}
                            onChange={(e) => handleMedicationChange(idx, 'medication_name', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.4rem 0.6rem',
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              borderRadius: '6px',
                              border: '1px solid var(--secondary-300)',
                            }}
                          />
                        </div>
                        <div style={{ flex: 1 }}>
                          <input
                            type="text"
                            placeholder="Dosage (e.g. 20 mg)"
                            value={med.dosage}
                            onChange={(e) => handleMedicationChange(idx, 'dosage', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.4rem 0.6rem',
                              fontSize: '0.8125rem',
                              borderRadius: '6px',
                              border: '1px solid var(--secondary-300)',
                            }}
                          />
                        </div>
                        <div style={{ flex: 1 }}>
                          <input
                            type="text"
                            placeholder="Frequency"
                            value={med.frequency}
                            onChange={(e) => handleMedicationChange(idx, 'frequency', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.4rem 0.6rem',
                              fontSize: '0.8125rem',
                              borderRadius: '6px',
                              border: '1px solid var(--secondary-300)',
                            }}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveMedication(idx)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--danger-600)',
                            cursor: 'pointer',
                            padding: '0.25rem',
                          }}
                          title="Remove item"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>

                      <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <div style={{ flex: 1 }}>
                          <input
                            type="text"
                            placeholder="Duration (e.g. 30 days)"
                            value={med.duration}
                            onChange={(e) => handleMedicationChange(idx, 'duration', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.35rem 0.5rem',
                              fontSize: '0.75rem',
                              borderRadius: '4px',
                              border: '1px solid var(--secondary-200)',
                            }}
                          />
                        </div>
                        <div style={{ flex: 2 }}>
                          <input
                            type="text"
                            placeholder="Instructions (e.g. Take with water in the morning)"
                            value={med.instructions || ''}
                            onChange={(e) => handleMedicationChange(idx, 'instructions', e.target.value)}
                            style={{
                              width: '100%',
                              padding: '0.35rem 0.5rem',
                              fontSize: '0.75rem',
                              borderRadius: '4px',
                              border: '1px solid var(--secondary-200)',
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
                <button
                  type="button"
                  onClick={handleReset}
                  className="btn btn-secondary"
                  disabled={isSaving}
                  style={{ fontSize: '0.875rem' }}
                >
                  Back to Upload
                </button>

                <button
                  type="button"
                  onClick={handleConfirmAndSave}
                  disabled={isSaving || draft.medications.length === 0}
                  className="btn btn-primary"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.75rem 1.5rem',
                    fontWeight: 600,
                  }}
                >
                  {isSaving ? (
                    <>
                      <Clock size={16} className="animate-spin" /> Saving to Records...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={16} /> Confirm & Save to Records
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* STEP 3: Success Confirmation Screen */}
          {saveSuccess && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                padding: '1rem 0',
                gap: '1.25rem',
              }}
            >
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--success-50)',
                  border: '2px solid var(--success-500)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--success-600)',
                }}
              >
                <CheckCircle2 size={36} />
              </div>

              <div>
                <h4 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary-900)', margin: '0 0 0.5rem 0' }}>
                  Prescription Successfully Recorded!
                </h4>
                <p style={{ fontSize: '0.875rem', color: 'var(--secondary-600)', maxWidth: '480px', margin: '0 auto' }}>
                  {saveSuccess.message}
                </p>
              </div>

              {/* Medication Schedule Preview */}
              {saveSuccess.medication_schedule && saveSuccess.medication_schedule.length > 0 && (
                <div
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    backgroundColor: 'var(--bg-main)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    border: '1px solid var(--secondary-200)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '0.8125rem', color: 'var(--secondary-800)', marginBottom: '0.5rem' }}>
                    <Pill size={16} color="var(--primary-600)" />
                    CareAI Medication Schedule Summary
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'var(--secondary-700)', lineHeight: 1.6 }}>
                    {saveSuccess.medication_schedule.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Drug Interaction Warnings */}
              {saveSuccess.interaction_warnings && saveSuccess.interaction_warnings.length > 0 && (
                <div
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    backgroundColor: 'var(--warning-50)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    border: '1px solid var(--warning-200)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '0.8125rem', color: 'var(--warning-900)', marginBottom: '0.5rem' }}>
                    <AlertTriangle size={16} color="var(--warning-700)" />
                    CareAI Pharmacotherapy Guidance & Warnings
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'var(--warning-800)', lineHeight: 1.5 }}>
                    {saveSuccess.interaction_warnings.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                type="button"
                onClick={handleModalClose}
                className="btn btn-primary"
                style={{ marginTop: '0.5rem', padding: '0.75rem 2rem', fontWeight: 600 }}
              >
                Done & Return to Assistant
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
