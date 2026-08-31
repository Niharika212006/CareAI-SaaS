import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import Button from '../common/Button';

export function AIErrorState({ error, onRetry }) {
  // Format user-friendly explanation
  let message = 'CareAI is temporarily unavailable. Please try again shortly.';
  if (typeof error === 'string') {
    message = error;
  } else if (error?.status === 503) {
    message = 'CareAI Assistant service is currently busy or experiencing high demand. Please try again in a few moments.';
  } else if (error?.status === 502) {
    message = 'CareAI Assistant received an unexpected response from the AI provider. Please retry your inquiry.';
  } else if (error?.message) {
    message = error.message;
  }

  return (
    <div
      className="animate-fade-in"
      style={{
        background: '#fff1f2',
        border: '1px solid #fecdd3',
        borderRadius: 'var(--radius-md)',
        padding: '1rem 1.25rem',
        margin: '1rem 0',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.625rem' }}>
        <AlertTriangle size={18} color="#e11d48" style={{ marginTop: '2px', flexShrink: 0 }} />
        <div style={{ fontSize: '0.875rem', color: '#9f1239', fontWeight: 500, lineHeight: 1.5 }}>
          {message}
        </div>
      </div>

      {onRetry && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            style={{
              borderColor: '#fda4af',
              color: '#be123c',
              background: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.375rem 0.75rem',
              fontSize: '0.8125rem',
            }}
          >
            <RefreshCw size={13} /> Retry Turn
          </Button>
        </div>
      )}
    </div>
  );
}

export default AIErrorState;
