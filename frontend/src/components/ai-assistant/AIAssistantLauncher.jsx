import React, { useState } from 'react';
import { Sparkles, MessageSquare } from 'lucide-react';
import useAuth from '../../hooks/useAuth';
import { USER_ROLES } from '../../utils/constants';
import AIAssistantChat from './AIAssistantChat';

const ROLE_LABELS = {
  [USER_ROLES.PATIENT]: 'CareAI Health Assistant',
  [USER_ROLES.DOCTOR]: 'CareAI Clinical Copilot',
  [USER_ROLES.LAB_TECHNICIAN]: 'CareAI Lab Assistant',
  [USER_ROLES.PHARMACY_STAFF]: 'CareAI Pharmacy Assistant',
  [USER_ROLES.ADMIN]: 'CareAI Operations Assistant',
};

export function AIAssistantLauncher() {
  const { isAuthenticated, role } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  if (!isAuthenticated) return null;

  const assistantLabel = ROLE_LABELS[role] || 'CareAI Assistant';

  return (
    <>
      {/* Floating Action Button */}
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 9990,
          display: 'flex',
          alignItems: 'center',
          gap: '0.625rem',
        }}
        className="ai-launcher-container"
      >
        {/* Hover Pill Tooltip */}
        {isHovered && !isOpen && (
          <div
            className="animate-fade-in"
            style={{
              background: 'rgba(15, 23, 42, 0.9)',
              color: '#ffffff',
              padding: '0.4rem 0.85rem',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.75rem',
              fontWeight: 600,
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              backdropFilter: 'blur(6px)',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
            }}
          >
            {assistantLabel} • Gemini Powered
          </div>
        )}

        <button
          type="button"
          onClick={() => setIsOpen(true)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          className="ai-launcher-btn"
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
            color: '#ffffff',
            border: 'none',
            boxShadow: '0 8px 24px rgba(13, 148, 136, 0.35)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            transition: 'transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease',
          }}
          title={assistantLabel}
        >
          <Sparkles size={24} className="sparkle-icon" />

          {/* Pulse Live Animation Ring */}
          <span
            style={{
              position: 'absolute',
              inset: '-3px',
              borderRadius: '50%',
              border: '2px solid rgba(20, 184, 166, 0.5)',
              animation: 'ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite',
              pointerEvents: 'none',
            }}
          />
        </button>
      </div>

      {/* Main Chat Modal */}
      <AIAssistantChat isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}

export default AIAssistantLauncher;
