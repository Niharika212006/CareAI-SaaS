import React from 'react';
import {
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Info,
  X,
  Pill,
  Utensils,
  AlertOctagon,
  Copy,
  CheckCircle,
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { formatDateTime } from '../../utils/formatters';

export function AISafetyReportModal({ report, onClose, prescriptionInfo }) {
  if (!report) return null;

  const getRiskBannerStyle = (risk) => {
    switch (risk) {
      case 'CRITICAL':
        return {
          bg: '#fff1f2',
          border: '1px solid #fecdd3',
          color: '#9f1239',
          iconColor: '#e11d48',
          badgeVariant: 'rose',
          title: 'Critical Safety Concerns Detected',
        };
      case 'HIGH':
        return {
          bg: '#fff7ed',
          border: '1px solid #fed7aa',
          color: '#9a3412',
          iconColor: '#ea580c',
          badgeVariant: 'amber',
          title: 'High-Risk Drug Interactions Identified',
        };
      case 'MODERATE':
        return {
          bg: '#fefce8',
          border: '1px solid #fef08a',
          color: '#854d0e',
          iconColor: '#ca8a04',
          badgeVariant: 'amber',
          title: 'Moderate Clinical Advisories Found',
        };
      case 'LOW':
        return {
          bg: '#f0fdf4',
          border: '1px solid #bbf7d0',
          color: '#166534',
          iconColor: '#16a34a',
          badgeVariant: 'teal',
          title: 'Low-Risk Dietary / Timing Advisories',
        };
      default:
        return {
          bg: '#f8fafc',
          border: '1px solid #e2e8f0',
          color: '#334155',
          iconColor: '#10b981',
          badgeVariant: 'green',
          title: 'No Potential Interactions Identified',
        };
    }
  };

  const banner = getRiskBannerStyle(report.overall_risk_level);

  const ddi = report.drug_drug_interactions || [];
  const dfi = report.drug_food_interactions || [];
  const dai = report.drug_allergy_interactions || [];
  const duplicates = (report.findings || []).filter((f) => f.category === 'DUPLICATE_MEDICATION');

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
          maxWidth: '740px',
          width: '100%',
          boxShadow: 'var(--shadow-xl)',
          overflow: 'hidden',
          maxHeight: '92vh',
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'var(--primary-100)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 800 }}>AI Prescription Safety Analysis</h3>
                <Badge variant={banner.badgeVariant}>{report.overall_risk_level} RISK</Badge>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--secondary-500)' }}>
                Prescription Ref: #{report.prescription_id || prescriptionInfo?.id || 'DIRECT'} • Evaluated on{' '}
                {formatDateTime(report.analyzed_at || new Date().toISOString())}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--secondary-400)',
              padding: '4px',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Overall Risk Summary Banner */}
          <div
            style={{
              backgroundColor: banner.bg,
              border: banner.border,
              borderRadius: 'var(--radius-md)',
              padding: '1rem 1.25rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.875rem',
            }}
          >
            {report.overall_risk_level === 'CRITICAL' || report.overall_risk_level === 'HIGH' ? (
              <ShieldAlert size={24} color={banner.iconColor} style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : report.overall_risk_level === 'NONE' ? (
              <ShieldCheck size={24} color={banner.iconColor} style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : (
              <AlertTriangle size={24} color={banner.iconColor} style={{ flexShrink: 0, marginTop: '2px' }} />
            )}

            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: banner.color, marginBottom: '2px' }}>
                {banner.title} ({report.total_findings} finding{report.total_findings === 1 ? '' : 's'})
              </div>
              <p style={{ fontSize: '0.8125rem', color: banner.color, lineHeight: 1.45, margin: 0 }}>
                {report.clinical_summary || report.summary}
              </p>
            </div>
          </div>

          {/* Finding Categories */}
          {report.total_findings === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '2rem 1rem',
                background: '#f8fafc',
                borderRadius: 'var(--radius-md)',
                border: '1px dashed var(--secondary-200)',
              }}
            >
              <CheckCircle size={32} color="var(--primary-600)" style={{ marginBottom: '0.5rem' }} />
              <div style={{ fontWeight: 700, fontSize: '0.9375rem' }}>No Known Contraindications Detected</div>
              <p style={{ color: 'var(--secondary-500)', fontSize: '0.8125rem', maxWidth: '480px', margin: '0.25rem auto 0' }}>
                No dangerous drug-drug interactions, food restrictions, allergy conflicts, or duplicate ingredients were found in the current demonstration database.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* 1. Drug-Allergy Contraindications */}
              {dai.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <AlertOctagon size={16} color="var(--accent-rose)" />
                    <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: 'var(--accent-rose)', textTransform: 'uppercase' }}>
                      Allergy Contraindications ({dai.length})
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {dai.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#fff1f2',
                          border: '1px solid #fecdd3',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.875rem', color: '#9f1239' }}>
                            {item.title || item.medications.join(' vs ')}
                          </span>
                          <Badge variant="rose">{item.severity}</Badge>
                        </div>
                        <p style={{ fontSize: '0.8125rem', color: '#881337', margin: '0 0 0.5rem' }}>
                          {item.explanation}
                        </p>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#9f1239', background: '#ffe4e6', padding: '0.35rem 0.6rem', borderRadius: '4px' }}>
                          💡 <strong>Clinical Guidance:</strong> {item.recommended_action}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 2. Drug-Drug Interactions */}
              {ddi.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Pill size={16} color="var(--accent-amber)" />
                    <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: 'var(--secondary-900)', textTransform: 'uppercase' }}>
                      Drug–Drug Interactions ({ddi.length})
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {ddi.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#ffffff',
                          border: '1px solid var(--secondary-200)',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                          boxShadow: 'var(--shadow-sm)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                            {item.title || item.medications.join(' + ')}
                          </span>
                          <Badge variant={item.severity === 'CRITICAL' || item.severity === 'HIGH' ? 'rose' : 'amber'}>
                            {item.severity}
                          </Badge>
                        </div>
                        <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-700)', margin: '0 0 0.5rem' }}>
                          {item.explanation}
                        </p>
                        <div style={{ fontSize: '0.75rem', color: 'var(--secondary-800)', background: '#f8fafc', padding: '0.35rem 0.6rem', borderRadius: '4px', border: '1px solid var(--secondary-100)' }}>
                          💡 <strong>Action:</strong> {item.recommended_action}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Drug-Food Interactions */}
              {dfi.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Utensils size={16} color="var(--primary-600)" />
                    <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: 'var(--secondary-900)', textTransform: 'uppercase' }}>
                      Dietary & Food Timing Advisories ({dfi.length})
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {dfi.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#ffffff',
                          border: '1px solid var(--secondary-200)',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                          boxShadow: 'var(--shadow-sm)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>
                            {item.title || item.medications[0]}
                          </span>
                          <Badge variant="teal">{item.severity}</Badge>
                        </div>
                        <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-700)', margin: '0 0 0.5rem' }}>
                          {item.explanation}
                        </p>
                        <div style={{ fontSize: '0.75rem', color: 'var(--secondary-800)', background: '#f8fafc', padding: '0.35rem 0.6rem', borderRadius: '4px' }}>
                          🥗 <strong>Dietary Timing:</strong> {item.recommended_action}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. Duplication Warnings */}
              {duplicates.length > 0 && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Copy size={16} color="var(--secondary-600)" />
                    <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: 'var(--secondary-900)', textTransform: 'uppercase' }}>
                      Therapeutic Duplication Notices ({duplicates.length})
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {duplicates.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#fffbeb',
                          border: '1px solid #fde68a',
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.875rem', color: '#92400e' }}>
                            {item.title}
                          </span>
                          <Badge variant="amber">{item.severity}</Badge>
                        </div>
                        <p style={{ fontSize: '0.8125rem', color: '#78350f', margin: '0 0 0.5rem' }}>
                          {item.explanation}
                        </p>
                        <div style={{ fontSize: '0.75rem', color: '#92400e', background: '#fef3c7', padding: '0.35rem 0.6rem', borderRadius: '4px' }}>
                          ⚠️ <strong>Action:</strong> {item.recommended_action}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Prominent Legal / Medical Safety Disclaimer */}
          <div
            style={{
              padding: '0.875rem 1rem',
              background: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.75rem',
              color: '#475569',
              lineHeight: 1.45,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontWeight: 700, marginBottom: '2px', color: '#334155' }}>
              <Info size={14} />
              <span>Clinical Decision Support Disclaimer</span>
            </div>
            {report.disclaimer}
          </div>
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid var(--secondary-200)',
            display: 'flex',
            justifyContent: 'flex-end',
            background: '#fafafa',
          }}
        >
          <Button variant="primary" onClick={onClose}>
            Close Report
          </Button>
        </div>
      </div>
    </div>
  );
}

export default AISafetyReportModal;
