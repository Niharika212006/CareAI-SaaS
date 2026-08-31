import React, { useState, useEffect } from 'react';
import {
  HeartPulse,
  AlertOctagon,
  Pill,
  Activity,
  X,
  Phone,
  Calendar,
  ShieldCheck,
  User,
  FolderOpen,
  FileText,
  ExternalLink,
  Download,
  Sparkles,
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';
import patientService from '../../services/patientService';
import medicalDocumentService from '../../services/medicalDocumentService';
import { DocumentAnalysisModal } from '../patient/DocumentAnalysisModal';
import { formatDate, formatDateTime } from '../../utils/formatters';

export function DoctorPatientSummaryModal({ patientId, onClose }) {
  const [summary, setSummary] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // AI Analysis View State
  const [viewingAnalysisDoc, setViewingAnalysisDoc] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState(false);

  useEffect(() => {
    if (patientId) {
      loadData();
    }
  }, [patientId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [summaryData, docsData] = await Promise.allSettled([
        patientService.getDoctorPatientSummary(patientId),
        medicalDocumentService.getPatientDocumentsForDoctor(patientId),
      ]);
      
      if (summaryData.status === 'fulfilled') {
        setSummary(summaryData.value);
      } else {
        throw new Error(summaryData.reason?.message || 'Failed to load summary');
      }

      if (docsData.status === 'fulfilled') {
        setDocuments(docsData.value?.items || []);
      }
    } catch (err) {
      console.error('Failed to load patient medical records:', err);
      setError(err.message || 'Failed to load patient medical records.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 110,
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
            background: 'linear-gradient(135deg, #f0fdfa 0%, #ffffff 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'var(--primary-100)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <HeartPulse size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 800 }}>Clinical Patient Medical Summary</h3>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                Treating Physician Access Protocol • Patient ID #{patientId}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-400)', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
              Loading patient medical record...
            </div>
          ) : error ? (
            <div
              style={{
                background: '#fff1f2',
                border: '1px solid #fecdd3',
                color: '#9f1239',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
              }}
            >
              {error}
            </div>
          ) : summary ? (
            <>
              {/* Demographics Banner */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '0.75rem',
                  padding: '1rem',
                  background: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--secondary-200)',
                  fontSize: '0.8125rem',
                }}
              >
                <div>
                  <div style={{ color: 'var(--secondary-500)', fontSize: '0.6875rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Patient Name
                  </div>
                  <strong style={{ fontSize: '0.9375rem' }}>{summary.full_name}</strong>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', fontSize: '0.6875rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Blood Group
                  </div>
                  <strong style={{ color: 'var(--primary-700)', fontSize: '0.9375rem' }}>
                    {summary.blood_group || 'Not recorded'}
                  </strong>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', fontSize: '0.6875rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Gender / DOB
                  </div>
                  <div>
                    {summary.gender || 'N/A'} • {summary.date_of_birth ? formatDate(summary.date_of_birth) : 'N/A'}
                  </div>
                </div>

                <div>
                  <div style={{ color: 'var(--secondary-500)', fontSize: '0.6875rem', textTransform: 'uppercase', fontWeight: 700 }}>
                    Smoking / Alcohol
                  </div>
                  <div>
                    {summary.smoking_status || 'N/A'} / {summary.alcohol_consumption || 'N/A'}
                  </div>
                </div>
              </div>

              {/* Section 1: Known Allergies */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <AlertOctagon size={16} color="var(--accent-rose)" />
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--accent-rose)', textTransform: 'uppercase' }}>
                    Allergies & Sensitivities ({summary.allergies?.length || 0})
                  </h4>
                </div>

                {summary.allergies && summary.allergies.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {summary.allergies.map((all, i) => (
                      <div
                        key={i}
                        style={{
                          background: '#fff1f2',
                          border: '1px solid #fecdd3',
                          borderRadius: '6px',
                          padding: '0.625rem 0.875rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <div>
                          <strong style={{ color: '#9f1239' }}>{all.name}</strong>
                          <span style={{ color: '#881337', marginLeft: '6px', fontSize: '0.75rem' }}>
                            ({all.type}) {all.reaction ? `— Reaction: ${all.reaction}` : ''}
                          </span>
                        </div>
                        <Badge variant="rose" style={{ fontSize: '0.6875rem' }}>{all.severity}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)', background: '#f8fafc', padding: '0.625rem', borderRadius: '6px' }}>
                    No known drug or food allergies recorded.
                  </div>
                )}
              </div>

              {/* Section 2: Chronic Conditions & Surgeries */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Activity size={16} color="var(--primary-700)" />
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--secondary-900)', textTransform: 'uppercase' }}>
                    Medical Conditions & Surgical History
                  </h4>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div style={{ background: '#ffffff', border: '1px solid var(--secondary-200)', borderRadius: '6px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', marginBottom: '4px' }}>
                      Chronic Conditions
                    </div>
                    {summary.chronic_conditions && summary.chronic_conditions.length > 0 ? (
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {summary.chronic_conditions.map((c, i) => (
                          <Badge key={i} variant="amber" style={{ fontSize: '0.75rem' }}>{c}</Badge>
                        ))}
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>None recorded</span>
                    )}
                  </div>

                  <div style={{ background: '#ffffff', border: '1px solid var(--secondary-200)', borderRadius: '6px', padding: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--secondary-500)', marginBottom: '4px' }}>
                      Prior Surgeries
                    </div>
                    {summary.surgeries && summary.surgeries.length > 0 ? (
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {summary.surgeries.map((s, i) => (
                          <Badge key={i} variant="slate" style={{ fontSize: '0.75rem' }}>{s}</Badge>
                        ))}
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--secondary-400)' }}>None recorded</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Section 3: Current Daily Medications */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Pill size={16} color="var(--primary-700)" />
                  <h4 style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--secondary-900)', textTransform: 'uppercase' }}>
                    Current Active Medications ({summary.current_medications?.length || 0})
                  </h4>
                </div>

                {summary.current_medications && summary.current_medications.length > 0 ? (
                  <div style={{ border: '1px solid var(--secondary-200)', borderRadius: '6px', overflow: 'hidden' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ background: 'var(--primary-50)', color: 'var(--primary-900)' }}>
                          <th style={{ padding: '0.4rem 0.625rem' }}>Medication</th>
                          <th style={{ padding: '0.4rem 0.625rem' }}>Dosage</th>
                          <th style={{ padding: '0.4rem 0.625rem' }}>Schedule</th>
                          <th style={{ padding: '0.4rem 0.625rem' }}>Instructions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.current_medications.map((med, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                            <td style={{ padding: '0.4rem 0.625rem', fontWeight: 700 }}>{med.name}</td>
                            <td style={{ padding: '0.4rem 0.625rem' }}>{med.dosage || '—'}</td>
                            <td style={{ padding: '0.4rem 0.625rem' }}>{med.frequency || '—'}</td>
                            <td style={{ padding: '0.4rem 0.625rem', color: 'var(--secondary-600)' }}>{med.instructions || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)', background: '#f8fafc', padding: '0.625rem', borderRadius: '6px' }}>
                    No active daily medications recorded by patient.
                  </div>
                )}
              </div>

              {/* Section 4: Uploaded Medical Documents & Lab Reports */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FolderOpen size={16} color="var(--primary-700)" />
                    <h4 style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--secondary-900)', textTransform: 'uppercase' }}>
                      Patient Health Records & Documents ({documents.length})
                    </h4>
                  </div>
                </div>

                {documents.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {documents.map((doc) => {
                      const handleViewAnalysis = async (doc) => {
                        setViewingAnalysisDoc(doc);
                        setIsAnalysisModalOpen(true);
                        setAnalysisLoading(true);
                        setAnalysisError(null);
                        try {
                          const data = await medicalDocumentService.getDocumentAnalysis(doc.id);
                          setAnalysisData(data);
                        } catch (err) {
                          console.error('Failed to load analysis:', err);
                          const msg = err.response?.data?.detail || err.message || 'No AI analysis found for this document yet.';
                          setAnalysisError(msg);
                        } finally {
                          setAnalysisLoading(false);
                        }
                      };

                      return (
                      <div
                        key={doc.id}
                        style={{
                          padding: '0.625rem 0.875rem',
                          borderRadius: '6px',
                          border: '1px solid var(--secondary-200)',
                          background: '#ffffff',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          gap: '0.75rem',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flex: 1, minWidth: 0 }}>
                          <FileText size={18} color="var(--primary-600)" style={{ flexShrink: 0 }} />
                          <div style={{ minWidth: 0, flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                              <span style={{ fontWeight: 700, fontSize: '0.8125rem', color: 'var(--secondary-900)' }}>
                                {doc.title}
                              </span>
                              <Badge variant="blue" style={{ fontSize: '0.6875rem', padding: '0.1rem 0.35rem' }}>
                                {doc.document_type.replace('_', ' ')}
                              </Badge>
                            </div>
                            <div style={{ fontSize: '0.6875rem', color: 'var(--secondary-400)', marginTop: '2px' }}>
                              {doc.file_name} • {formatDateTime(doc.created_at)}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexShrink: 0 }}>
                          <button
                            onClick={() => handleViewAnalysis(doc)}
                            title="View AI Clinical Insights"
                            style={{
                              padding: '0.35rem 0.6rem',
                              borderRadius: '4px',
                              border: '1px solid #c7d2fe',
                              background: '#eef2ff',
                              color: '#4338ca',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                              fontSize: '0.6875rem',
                              fontWeight: 600,
                            }}
                          >
                            <Sparkles size={12} color="#4f46e5" />
                            <span>AI Insights</span>
                          </button>
                          <button
                            onClick={() => medicalDocumentService.viewDocument(doc.id)}
                            title="View Document"
                            style={{
                              padding: '0.35rem',
                              borderRadius: '4px',
                              border: '1px solid var(--secondary-200)',
                              background: '#ffffff',
                              color: 'var(--secondary-700)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                            }}
                          >
                            <ExternalLink size={13} />
                          </button>
                          <button
                            onClick={() => medicalDocumentService.downloadDocument(doc.id, doc.file_name)}
                            title="Download Document"
                            style={{
                              padding: '0.35rem',
                              borderRadius: '4px',
                              border: '1px solid var(--secondary-200)',
                              background: '#ffffff',
                              color: 'var(--primary-600)',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                            }}
                          >
                            <Download size={13} />
                          </button>
                        </div>
                      </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)', background: '#f8fafc', padding: '0.625rem', borderRadius: '6px' }}>
                    No medical documents or lab reports uploaded by this patient.
                  </div>
                )}
              </div>

              {/* Emergency Contact & Notes */}
              {(summary.emergency_contact || summary.medical_history_summary) && (
                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid var(--secondary-200)', fontSize: '0.8125rem' }}>
                  {summary.emergency_contact && (
                    <div style={{ marginBottom: summary.medical_history_summary ? '4px' : 0 }}>
                      <span style={{ color: 'var(--secondary-500)' }}>Emergency Contact:</span> <strong>{summary.emergency_contact}</strong>
                    </div>
                  )}
                  {summary.medical_history_summary && (
                    <div style={{ color: 'var(--secondary-700)' }}>
                      <span style={{ color: 'var(--secondary-500)' }}>Provider Notes:</span> {summary.medical_history_summary}
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end', background: '#fafafa' }}>
          <Button variant="primary" onClick={onClose}>
            Close Summary
          </Button>
        </div>
      </div>

      <DocumentAnalysisModal
        isOpen={isAnalysisModalOpen}
        onClose={() => {
          setIsAnalysisModalOpen(false);
          setAnalysisData(null);
          setAnalysisError(null);
        }}
        analysis={analysisData}
        document={viewingAnalysisDoc}
        isLoading={analysisLoading}
        error={analysisError}
        onRetry={() => viewingAnalysisDoc && handleViewAnalysis(viewingAnalysisDoc)}
      />
    </div>
  );
}

export default DoctorPatientSummaryModal;
