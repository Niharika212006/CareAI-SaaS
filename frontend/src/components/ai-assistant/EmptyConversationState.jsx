import React from 'react';
import {
  Sparkles,
  HeartHandshake,
  Stethoscope,
  FlaskConical,
  Pill,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';
import { USER_ROLES } from '../../utils/constants';

const ROLE_CONFIGS = {
  [USER_ROLES.PATIENT]: {
    name: 'CareAI Health Assistant',
    subtitle: 'Personalized health records, active prescription schedules, and clinical guidance.',
    icon: HeartHandshake,
    accentColor: '#0d9488',
    gradient: 'linear-gradient(135deg, #0d9488 0%, #0284c7 100%)',
    suggestions: [
      'Summarize my active prescriptions and daily dosage schedule',
      'Explain my upcoming doctor appointments and preparation steps',
      'Review my latest laboratory reports and biomarker values',
      'Upload and review a new prescription document',
    ],
  },
  [USER_ROLES.DOCTOR]: {
    name: 'CareAI Clinical Copilot',
    subtitle: 'Clinical decision support, patient history synthesis, and diagnostic reference.',
    icon: Stethoscope,
    accentColor: '#4f46e5',
    gradient: 'linear-gradient(135deg, #4f46e5 0%, #0284c7 100%)',
    suggestions: [
      'Summarize my clinical appointment schedule for today',
      'Show patients with upcoming consultations requiring chart review',
      'Review pending lab requisitions and diagnostic workups',
      'Draft structured clinical encounter SOAP notes',
    ],
  },
  [USER_ROLES.LAB_TECHNICIAN]: {
    name: 'CareAI Lab Assistant',
    subtitle: 'Diagnostic testing protocols, reference intervals, and specimen workflow assistance.',
    icon: FlaskConical,
    accentColor: '#7c3aed',
    gradient: 'linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)',
    suggestions: [
      'Show my pending specimen analysis queue',
      'Review critical panic values and abnormal diagnostic flags',
      'Check specimen accessioning guidelines for blood chemistry',
      'Show lab orders awaiting verification in my department',
    ],
  },
  [USER_ROLES.PHARMACY_STAFF]: {
    name: 'CareAI Pharmacy Assistant',
    subtitle: 'Medication safety, pharmacotherapy interaction analysis, and formulary advisory.',
    icon: Pill,
    accentColor: '#0284c7',
    gradient: 'linear-gradient(135deg, #0284c7 0%, #0d9488 100%)',
    suggestions: [
      'Show prescriptions waiting for verification in the queue',
      'Check prescriptions ready for patient dispensing',
      'Analyze drug-drug interactions for multi-medication regimens',
      'Review prescription fulfillment audit log',
    ],
  },
  [USER_ROLES.ADMIN]: {
    name: 'CareAI Operations Assistant',
    subtitle: 'Platform analytics, operational throughput, and compliance oversight.',
    icon: ShieldCheck,
    accentColor: '#d97706',
    gradient: 'linear-gradient(135deg, #d97706 0%, #475569 100%)',
    suggestions: [
      'Provide platform overview: user counts by role and doctor approvals',
      'How many appointments are scheduled across all departments today?',
      'What is the breakdown of prescriptions and lab orders platform-wide?',
      'Show platform operational health and governance metrics',
    ],
  },
};

export function EmptyConversationState({ role, onSelectPrompt, onUploadClick = null }) {
  const config = ROLE_CONFIGS[role] || ROLE_CONFIGS[USER_ROLES.PATIENT];
  const IconComponent = config.icon;

  const handlePromptClick = (prompt) => {
    if (prompt === 'Upload and review a new prescription document' && onUploadClick) {
      onUploadClick();
      return;
    }
    onSelectPrompt(prompt);
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '2.5rem 1.5rem',
        margin: 'auto 0',
      }}
    >
      <div
        style={{
          width: '64px',
          height: '64px',
          borderRadius: '18px',
          background: config.gradient,
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
          marginBottom: '1.25rem',
        }}
      >
        <IconComponent size={32} />
      </div>

      <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary-900)', marginBottom: '0.5rem' }}>
        {config.name}
      </h3>
      <p
        style={{
          fontSize: '0.875rem',
          color: 'var(--secondary-500)',
          maxWidth: '460px',
          lineHeight: 1.5,
          marginBottom: '2rem',
        }}
      >
        {config.subtitle}
      </p>

      {/* Suggested Quick Prompts Grid */}
      <div style={{ width: '100%', maxWidth: '540px' }}>
        <div
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--secondary-500)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '0.75rem',
            textAlign: 'left',
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
          }}
        >
          <Sparkles size={13} color={config.accentColor} /> Suggested Prompts
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '0.625rem',
          }}
        >
          {config.suggestions.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              className="suggestion-prompt-btn"
              onClick={() => handlePromptClick(prompt)}
              style={{
                background: '#ffffff',
                border: '1px solid var(--secondary-200)',
                borderRadius: 'var(--radius-md)',
                padding: '0.75rem 1rem',
                textAlign: 'left',
                fontSize: '0.8125rem',
                color: 'var(--secondary-800)',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <span>{prompt}</span>
              <ArrowRight size={14} style={{ color: config.accentColor, flexShrink: 0 }} />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default EmptyConversationState;
