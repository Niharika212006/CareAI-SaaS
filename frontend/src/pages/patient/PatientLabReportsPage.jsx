import React, { useState, useEffect, useCallback } from 'react';
import {
  FlaskConical,
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  Printer,
  ShieldCheck,
  X,
  Stethoscope,
  ChevronRight,
} from 'lucide-react';
import Card from '../../components/common/Card';
import Badge from '../../components/common/Badge';
import Button from '../../components/common/Button';
import useAuth from '../../hooks/useAuth';
import labService from '../../services/labService';

export function PatientLabReportsPage() {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedReport, setSelectedReport] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadReports = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await labService.getPatientReports();
      setReports(res || []);
    } catch (err) {
      setError(err.message || 'Failed to load your diagnostic reports.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handleOpenDetail = async (orderId) => {
    try {
      setDetailLoading(true);
      const report = await labService.getPatientReportDetail(orderId);
      setSelectedReport(report);
      setDetailModalOpen(true);
    } catch (err) {
      alert(err.message || 'Failed to fetch report details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0d9488 0%, #0284c7 100%)',
          color: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          padding: '2rem',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.2)', padding: '0.5rem', borderRadius: '10px' }}>
            <FlaskConical size={24} color="#ffffff" />
          </div>
          <Badge variant="teal" style={{ background: '#ffffff', color: '#0d9488', fontWeight: 700 }}>
            Patient Diagnostic Portal
          </Badge>
        </div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
          My Diagnostic Laboratory Reports
        </h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.85)', margin: 0, fontSize: '0.9375rem' }}>
          View verified laboratory findings, track your biometric markers over time, and download official medical reports.
        </p>
      </div>

      {/* Reports List */}
      <Card className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={20} color="#0d9488" /> Released Laboratory Reports
          </h3>
          <span style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)' }}>
            {reports.length} report(s) available
          </span>
        </div>

        {error && (
          <div style={{ background: '#fff1f2', border: '1px solid #fecdd3', color: '#be123c', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} /> {error}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <div>Loading your diagnostic records...</div>
          </div>
        ) : reports.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--secondary-500)' }}>
            <FlaskConical size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.4 }} />
            <div style={{ fontWeight: 600 }}>No released laboratory reports yet.</div>
            <p style={{ fontSize: '0.8125rem', marginTop: '0.25rem' }}>
              When your doctor orders diagnostic tests and results are verified by the lab, they will appear here.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {reports.map((report) => (
              <div
                key={report.id}
                style={{
                  background: '#ffffff',
                  border: '1px solid var(--secondary-200)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.25rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  boxShadow: 'var(--shadow-sm)',
                  transition: 'border-color 0.15s ease',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--secondary-900)' }}>
                      Laboratory Report #{report.id}
                    </span>
                    <Badge variant="green">Verified & Released</Badge>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--secondary-600)', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <span>Ordered by: <strong>{report.doctor_name}</strong></span>
                    <span>Released: {report.released_at ? new Date(report.released_at).toLocaleDateString() : 'Recent'}</span>
                    {report.verified_by_name && (
                      <span>Verified by: <em>{report.verified_by_name}</em></span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                    {report.results.map((r, idx) => (
                      <span
                        key={idx}
                        style={{
                          background: 'var(--secondary-100)',
                          color: 'var(--secondary-800)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 500,
                        }}
                      >
                        {r.test_name}: {r.numeric_value ?? r.text_value} {r.unit || ''}
                      </span>
                    ))}
                  </div>
                </div>

                <Button
                  variant="outline"
                  onClick={() => handleOpenDetail(report.id)}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}
                >
                  <FileText size={15} /> View Full Report <ChevronRight size={14} />
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* ------------------------------------------------------------- */}
      {/* MODAL: FORMAL DIAGNOSTIC REPORT DETAIL (PRINTABLE) */}
      {/* ------------------------------------------------------------- */}
      {detailModalOpen && selectedReport && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }} className="animate-fade-in">
          <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', maxWidth: '780px', width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: 'var(--shadow-lg)', overflow: 'hidden' }}>
            {/* Modal Header */}
            <div style={{ padding: '1.25rem 1.75rem', borderBottom: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FlaskConical size={22} color="#0d9488" />
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0 }}>
                  CareAI Diagnostic Laboratory Report
                </h3>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <Button variant="outline" size="sm" onClick={handlePrint} style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <Printer size={14} /> Print Report
                </Button>
                <button type="button" onClick={() => setDetailModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--secondary-500)' }}>
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Printable Content Body */}
            <div style={{ padding: '1.75rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Header Meta Box */}
              <div style={{ border: '1px solid var(--secondary-200)', borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem', background: 'var(--bg-main)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Patient</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>{user?.full_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>{user?.email}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Ordering Physician</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>{selectedReport.doctor_name}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>{selectedReport.doctor_specialization || 'Clinical Specialist'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Requisition ID</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>#{selectedReport.id}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Priority: {selectedReport.priority}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>Verification Date</div>
                  <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>
                    {selectedReport.released_at ? new Date(selectedReport.released_at).toLocaleDateString() : 'Verified'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#059669', fontWeight: 600 }}>Status: Released</div>
                </div>
              </div>

              {/* Diagnostic Results Table */}
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, marginBottom: '0.75rem', color: 'var(--secondary-900)' }}>
                  Diagnostic Findings
                </h4>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--secondary-200)', color: 'var(--secondary-600)', textAlign: 'left', background: 'var(--secondary-50)' }}>
                      <th style={{ padding: '0.625rem 0.75rem' }}>Test Name</th>
                      <th style={{ padding: '0.625rem 0.75rem' }}>Category</th>
                      <th style={{ padding: '0.625rem 0.75rem' }}>Observed Value</th>
                      <th style={{ padding: '0.625rem 0.75rem' }}>Reference Range</th>
                      <th style={{ padding: '0.625rem 0.75rem', textAlign: 'right' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedReport.results.map((r, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--secondary-100)' }}>
                        <td style={{ padding: '0.75rem', fontWeight: 600 }}>{r.test_name}</td>
                        <td style={{ padding: '0.75rem', color: 'var(--secondary-600)', fontSize: '0.8125rem' }}>{r.category}</td>
                        <td style={{ padding: '0.75rem', fontWeight: 700, color: r.is_critical ? '#e11d48' : 'inherit' }}>
                          {r.numeric_value ?? r.text_value} {r.unit || ''}
                        </td>
                        <td style={{ padding: '0.75rem', color: 'var(--secondary-500)', fontSize: '0.8125rem' }}>
                          {r.reference_range || '-'}
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                          <Badge variant={r.is_critical ? 'rose' : r.result_flag === 'NORMAL' ? 'green' : 'amber'}>
                            {r.result_flag}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Disclaimer */}
              <div style={{ background: 'var(--secondary-50)', border: '1px solid var(--secondary-200)', borderRadius: 'var(--radius-md)', padding: '0.875rem 1rem', fontSize: '0.75rem', color: 'var(--secondary-600)', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <ShieldCheck size={16} color="var(--primary-600)" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <strong>Medical Disclaimer:</strong> This laboratory report has been verified and released by authorized clinical staff.
                  Results should always be interpreted in the context of clinical history and symptoms by your attending physician.
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '1rem 1.75rem', borderTop: '1px solid var(--secondary-200)', display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="primary" onClick={() => setDetailModalOpen(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PatientLabReportsPage;
