import React from 'react';
import { Sparkles } from 'lucide-react';

export function AILoadingIndicator() {
  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        margin: '1rem 0',
      }}
    >
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
          boxShadow: '0 2px 8px rgba(13, 148, 136, 0.25)',
          flexShrink: 0,
        }}
      >
        <Sparkles size={16} className="animate-spin" />
      </div>

      <div
        style={{
          background: '#ffffff',
          border: '1px solid var(--secondary-200)',
          borderRadius: '14px 14px 14px 2px',
          padding: '0.875rem 1.25rem',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.625rem',
        }}
      >
        <span style={{ fontSize: '0.875rem', color: 'var(--secondary-700)', fontWeight: 500 }}>
          CareAI is thinking...
        </span>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <span className="typing-dot" style={{ animationDelay: '0ms' }} />
          <span className="typing-dot" style={{ animationDelay: '200ms' }} />
          <span className="typing-dot" style={{ animationDelay: '400ms' }} />
        </div>
      </div>
    </div>
  );
}

export default AILoadingIndicator;
