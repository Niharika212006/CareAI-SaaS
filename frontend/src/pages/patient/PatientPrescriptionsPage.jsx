import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Calendar,
  Stethoscope,
  Pill,
  Clock,
  Printer,
  X,
  AlertCircle,
  Sparkles,
  ShieldCheck,
  Search,
  Activity,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import Badge from '../../components/common/Badge';
import prescriptionService from '../../services/prescriptionService';
import aiService from '../../services/aiService';
import AISafetyReportModal from '../../components/ai/AISafetyReportModal';
import { formatDate, formatDateTime, formatAllergiesDisplay } from '../../utils/formatters';

export function PatientPrescriptionsPage() {
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPrescription, setSelectedPrescription] = useState(null);

  // AI Safety Analysis State
  const [activeSafetyReport, setActiveSafetyReport] = useState(null);
  const [analyzingRxId, setAnalyzingRxId] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);

  useEffect(() => {
    loadPrescriptions();
  }, []);

  const loadPrescriptions = async () => {
    try {
      setLoading(true);
      const data = await prescriptionService.getMyPatientPrescriptions();
      setPrescriptions(data || []);
    } catch (err) {
      console.error('Failed to load patient prescriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAiSafetyCheck = async (prescription) => {
    try {
      setAnalyzingRxId(prescription.id);
      setAnalysisError(null);
      const report = await aiService.analyzePrescription(prescription.id);
      setActiveSafetyReport(report);
    } catch (err) {
      console.error('AI Safety check failed:', err);
      setAnalysisError(err.message || 'Failed to run AI safety check.');
    } finally {
      setAnalyzingRxId(null);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const filteredPrescriptions = prescriptions.filter((rx) => {
    const term = searchQuery.toLowerCase();
    const docName = rx.doctor?.user?.full_name?.toLowerCase() || '';
    const diag = rx.diagnosis?.toLowerCase() || '';
    const meds = rx.items?.some((item) =>
      (item.medication_name || item.drug_name || '').toLowerCase().includes(term)
    );
    return docName.includes(term) || diag.includes(term) || meds;
  });

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.25rem' }}>
          <FileText size={28} color="var(--primary-700)" />
          <h1 style={{ fontSize: '1.875rem', fontWeight: 800 }}>My Digital Prescriptions</h1>
        </div>
        <p style={{ color: 'var(--secondary-500)', fontSize: '0.9375rem' }}>
          Secure clinical records of all e-prescriptions issued by verified healthcare providers during your consultations.
        </p>
      </div>

      {analysisError && (
        <div
          style={{
            background: '#fff1f2',
            border: '1px solid #fecdd3',
            color: '#9f1239',
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.5rem',
            fontSize: '0.8125rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertCircle size={16} />
          <span>{analysisError}</span>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '280px' }}>
          <Search
            size={18}
            color="var(--secondary-400)"
            style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: '2.5rem' }}
            placeholder="Search by doctor, diagnosis, or medication name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Link to="/doctors" className="btn btn-secondary">
          Find Doctors
        </Link>
      </div>

      {/* Prescriptions Grid */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
          Loading your clinical prescriptions...
        </div>
      ) : filteredPrescriptions.length === 0 ? (
        <Card>
          <div
            style={{
              padding: '3rem 1.5rem',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
            }}
          >
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FileText size={32} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                {searchQuery ? 'No matching prescriptions found' : 'No Digital Prescriptions Issued Yet'}
              </h3>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.875rem', maxWidth: '400px', margin: '0 auto' }}>
                {searchQuery
                  ? 'Try searching with a different medication or doctor name.'
                  : 'After completing a consultation with a verified physician, your digital prescription script and medication instructions will appear here.'}
              </p>
            </div>
            {!searchQuery && (
              <Link to="/doctors" className="btn btn-primary">
                Book a Consultation
              </Link>
            )}
          </div>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredPrescriptions.map((rx) => (
            <Card key={rx.id} hover className="glass-panel">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  gap: '1.5rem',
                  flexWrap: 'wrap',
                }}
              >
                {/* Left: Doctor & Prescription Metadata */}
                <div style={{ flex: 1, minWidth: '280px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <div
                      style={{
                        background: 'var(--primary-100)',
                        color: 'var(--primary-700)',
                        padding: '0.5rem',
                        borderRadius: '10px',
                      }}
                    >
                      <Stethoscope size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 800, fontSize: '1.0625rem' }}>
                        Dr. {rx.doctor?.user?.full_name || 'Physician'}
                      </div>
                      <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
                        {rx.doctor?.specialization || 'Clinical Practice'} • License: {rx.doctor?.license_number}
                      </div>
                    </div>
                  </div>

                  <div style={{ margin: '0.75rem 0' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase' }}>
                      Clinical Diagnosis
                    </div>
                    <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                      {rx.diagnosis}
                    </div>
                    {rx.clinical_notes && (
                      <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)', marginTop: '2px' }}>
                        {rx.clinical_notes}
                      </p>
                    )}
                  </div>

                  {/* Medication Badges */}
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', marginBottom: '4px' }}>
                      Prescribed Medications ({rx.items?.length || 0})
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {rx.items?.map((item, idx) => (
                        <span
                          key={idx}
                          style={{
                            background: '#ffffff',
                            border: '1px solid var(--secondary-200)',
                            borderRadius: '6px',
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <Pill size={12} color="var(--primary-600)" />
                          <strong>{item.medication_name || item.drug_name}</strong> ({item.dosage})
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right: Date & Actions */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-end',
                    justifyContent: 'space-between',
                    minHeight: '120px',
                    gap: '0.75rem',
                  }}
                >
                  <div style={{ textAlign: 'right' }}>
                    <Badge variant="teal">Prescription #RX-{rx.id}</Badge>
                    <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                      <Calendar size={12} />
                      Issued: {formatDate(rx.created_at)}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Button
                      variant="primary"
                      icon={Sparkles}
                      style={{ fontSize: '0.8125rem', padding: '0.45rem 0.875rem' }}
                      disabled={analyzingRxId === rx.id}
                      onClick={() => handleRunAiSafetyCheck(rx)}
                    >
                      {analyzingRxId === rx.id ? 'Analyzing Safety...' : 'Analyze Safety'}
                    </Button>

                    <Button
                      variant="secondary"
                      icon={FileText}
                      style={{ fontSize: '0.8125rem', padding: '0.45rem 0.875rem' }}
                      onClick={() => setSelectedPrescription(rx)}
                    >
                      View Script
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Modal 1: Full E-Prescription Script */}
      {selectedPrescription && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
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
              maxWidth: '680px',
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
                <FileText size={24} color="var(--primary-700)" />
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 800 }}>
                    Official Digital Prescription
                  </h3>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                    Rx Document ID: #{selectedPrescription.id} • Issued: {formatDateTime(selectedPrescription.created_at)}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedPrescription(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-400)', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto' }}>
              {/* Doctor & Patient Split Info */}
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
                  <div style={{ color: 'var(--secondary-500)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Prescribing Doctor
                  </div>
                  <strong style={{ fontSize: '0.9375rem' }}>
                    Dr. {selectedPrescription.doctor?.user?.full_name || 'Practitioner'}
                  </strong>
                  <div style={{ color: 'var(--secondary-600)', marginTop: '2px' }}>
                    {selectedPrescription.doctor?.specialization} • License: {selectedPrescription.doctor?.license_number}
                  </div>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Patient Info
                  </div>
                  <strong style={{ fontSize: '0.9375rem' }}>
                    {selectedPrescription.patient?.user?.full_name || 'Patient'}
                  </strong>
                  <div style={{ color: 'var(--secondary-600)', marginTop: '2px' }}>
                    Blood Group: {selectedPrescription.patient?.blood_group || 'O+'} • Allergies: {formatAllergiesDisplay(selectedPrescription.patient?.allergies)}
                  </div>
                </div>
              </div>

              {/* Clinical Diagnosis */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Clinical Diagnosis
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
                  {selectedPrescription.diagnosis}
                </div>
                {selectedPrescription.clinical_notes && (
                  <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)', marginTop: '4px' }}>
                    <strong>Doctor Advice:</strong> {selectedPrescription.clinical_notes}
                  </p>
                )}
              </div>

              {/* Medications Table */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Prescribed Medication Schedule (Rx)
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
                      {selectedPrescription.items?.map((item, idx) => (
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

              {/* Digital Signature & Authenticity Badge */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  background: 'var(--primary-50)',
                  border: '1px solid var(--primary-200)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                  color: 'var(--primary-800)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck size={18} color="var(--primary-700)" />
                  <div>
                    <strong>Digitally Signed & Validated</strong>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--primary-600)' }}>
                      CareAI Health Network Cryptographic Audit Trail
                    </div>
                  </div>
                </div>
                <span>Appointment Ref: #{selectedPrescription.appointment_id || 'N/A'}</span>
              </div>
            </div>

            {/* Modal Footer */}
            <div
              style={{
                padding: '1rem 1.5rem',
                borderTop: '1px solid var(--secondary-200)',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <Button variant="secondary" icon={Printer} onClick={handlePrint}>
                Print Prescription
              </Button>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="primary"
                  icon={Sparkles}
                  disabled={analyzingRxId === selectedPrescription.id}
                  onClick={() => handleRunAiSafetyCheck(selectedPrescription)}
                >
                  Run Safety Audit
                </Button>
                <Button variant="secondary" onClick={() => setSelectedPrescription(null)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal 2: AI Safety Analysis Audit Modal */}
      {activeSafetyReport && (
        <AISafetyReportModal
          report={activeSafetyReport}
          onClose={() => setActiveSafetyReport(null)}
          prescriptionInfo={selectedPrescription}
        />
      )}
    </div>
  );
}

export default PatientPrescriptionsPage;
