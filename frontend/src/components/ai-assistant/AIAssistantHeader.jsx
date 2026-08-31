import React from 'react';
import {
  Sparkles,
  X,
  Plus,
  PanelLeft,
  Minimize2,
  HeartHandshake,
  Stethoscope,
  FlaskConical,
  Pill,
  ShieldCheck,
} from 'lucide-react';
import { USER_ROLES } from '../../utils/constants';

const ROLE_TITLES = {
  [USER_ROLES.PATIENT]: { name: 'CareAI Health Assistant', icon: HeartHandshake, badge: 'Patient Portal' },
  [USER_ROLES.DOCTOR]: { name: 'CareAI Clinical Copilot', icon: Stethoscope, badge: 'Doctor Copilot' },
  [USER_ROLES.LAB_TECHNICIAN]: { name: 'CareAI Lab Assistant', icon: FlaskConical, badge: 'Lab Workspace' },
  [USER_ROLES.PHARMACY_STAFF]: { name: 'CareAI Pharmacy Assistant', icon: Pill, badge: 'Pharmacy Dispensary' },
  [USER_ROLES.ADMIN]: { name: 'CareAI Operations Assistant', icon: ShieldCheck, badge: 'Operations Portal' },
};

export function AIAssistantHeader({
  role,
  onClose,
  onNewConversation,
  isSidebarOpen,
  onToggleSidebar,
}) {
  const roleConfig = ROLE_TITLES[role] || ROLE_TITLES[USER_ROLES.PATIENT];
  const IconComponent = roleConfig.icon;

  return (
    <div
      style={{
        padding: '0.875rem 1.25rem',
        borderBottom: '1px solid var(--secondary-200)',
        background: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
      }}
    >
      {/* Left Title & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          type="button"
          onClick={onToggleSidebar}
          className="btn-icon-subtle"
          style={{
            background: isSidebarOpen ? 'var(--secondary-100)' : 'transparent',
            border: '1px solid var(--secondary-200)',
            borderRadius: '8px',
            padding: '0.375rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--secondary-700)',
          }}
          title={isSidebarOpen ? 'Hide conversation history' : 'Show conversation history'}
        >
          <PanelLeft size={16} />
        </button>

        <div
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 6px rgba(13, 148, 136, 0.25)',
          }}
        >
          <IconComponent size={18} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'var(--secondary-900)' }}>
              {roleConfig.name}
            </span>
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                color: 'var(--primary-700)',
                background: 'var(--primary-50)',
                border: '1px solid var(--primary-100)',
                borderRadius: '4px',
                padding: '1px 6px',
              }}
            >
              {roleConfig.badge}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.6875rem', color: 'var(--secondary-500)' }}>
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: '#10b981',
                boxShadow: '0 0 6px #10b981',
                display: 'inline-block',
              }}
            />
            <span>Gemini AI Connected</span>
          </div>
        </div>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <button
          type="button"
          onClick={onNewConversation}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            background: 'var(--primary-50)',
            color: 'var(--primary-700)',
            border: '1px solid var(--primary-200)',
            borderRadius: '8px',
            padding: '0.375rem 0.75rem',
            fontSize: '0.75rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          title="Start new conversation"
        >
          <Plus size={14} /> New Chat
        </button>

        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            borderRadius: '8px',
            padding: '0.375rem',
            color: 'var(--secondary-500)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 0.15s ease',
          }}
          title="Close Assistant"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  );
}

export default AIAssistantHeader;
