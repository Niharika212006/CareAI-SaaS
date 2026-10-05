import React, { useState } from 'react';
import { Sparkles, User as UserIcon, AlertTriangle, Clock, ShieldCheck, FileText, ChevronDown, ChevronUp } from 'lucide-react';

export function ChatMessage({ message, isLastTurn }) {
  const isUser = message.sender === 'USER';
  const hasEmergencyAlert = message.safety_metadata?.emergency_symptom_detected;
  const [showSources, setShowSources] = useState(false);

  const sources = message.sources || message.safety_metadata?.sources || [];
  const hasSources = !isUser && Array.isArray(sources) && sources.length > 0;
  const ragUsed = !isUser && (hasSources || message.safety_metadata?.rag_used);

  const formattedTime = message.created_at
    ? new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : null;

  return (
    <div
      className="animate-fade-in"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        margin: '0.75rem 0',
        width: '100%',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
          gap: '0.625rem',
          maxWidth: '88%',
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '10px',
            background: isUser
              ? 'linear-gradient(135deg, var(--secondary-700) 0%, var(--secondary-900) 100%)'
              : 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: isUser ? 'var(--shadow-sm)' : '0 2px 8px rgba(13, 148, 136, 0.25)',
          }}
        >
          {isUser ? <UserIcon size={16} /> : <Sparkles size={16} />}
        </div>

        {/* Message Bubble Container */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', width: '100%' }}>
          {/* Main Bubble */}
          <div
            style={{
              padding: '0.875rem 1.125rem',
              borderRadius: isUser ? '16px 16px 2px 16px' : '16px 16px 16px 2px',
              background: isUser
                ? 'linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%)'
                : '#ffffff',
              color: isUser ? '#ffffff' : 'var(--secondary-900)',
              border: isUser ? 'none' : '1px solid var(--secondary-200)',
              boxShadow: isUser ? '0 2px 8px rgba(13, 148, 136, 0.2)' : 'var(--shadow-sm)',
              fontSize: '0.875rem',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {message.content}
          </div>

          {/* Emergency Safety Alert Card if flagged */}
          {hasEmergencyAlert && (
            <div
              style={{
                background: '#fff1f2',
                border: '1px solid #fecdd3',
                borderRadius: '10px',
                padding: '0.75rem 1rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.5rem',
                color: '#9f1239',
                fontSize: '0.8125rem',
                fontWeight: 600,
              }}
            >
              <AlertTriangle size={16} color="#e11d48" style={{ marginTop: '2px', flexShrink: 0 }} />
              <div>
                {message.safety_metadata?.triage_guidance ||
                  'Emergency warning: Please seek immediate medical attention or call emergency services.'}
              </div>
            </div>
          )}

          {/* Grounded Knowledge Base Sources Card */}
          {hasSources && (
            <div
              style={{
                marginTop: '0.25rem',
                background: 'rgba(240, 253, 250, 0.85)',
                border: '1px solid #ccfbf1',
                borderRadius: '10px',
                padding: '0.5rem 0.75rem',
                fontSize: '0.75rem',
              }}
            >
              <div
                onClick={() => setShowSources((prev) => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  userSelect: 'none',
                  color: 'var(--primary-700)',
                  fontWeight: 600,
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <ShieldCheck size={14} color="var(--primary-600)" />
                  Grounded in Medical Knowledge ({sources.length} {sources.length === 1 ? 'Source' : 'Sources'})
                </span>
                {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </div>
              {showSources && (
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                  {sources.map((src, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.375rem 0.5rem',
                        background: '#ffffff',
                        border: '1px solid #e6fffa',
                        borderRadius: '6px',
                        fontSize: '0.6875rem',
                        gap: '0.5rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', overflow: 'hidden' }}>
                        <FileText size={12} color="var(--primary-600)" style={{ flexShrink: 0 }} />
                        <span
                          style={{
                            fontWeight: 600,
                            color: 'var(--secondary-800)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {src.document_name}
                        </span>
                        {src.page && (
                          <span style={{ color: 'var(--secondary-500)', fontSize: '0.625rem', flexShrink: 0 }}>
                            (p. {src.page})
                          </span>
                        )}
                      </div>
                      <span
                        style={{
                          background: '#f0fdf4',
                          color: '#15803d',
                          padding: '1px 6px',
                          borderRadius: '4px',
                          fontWeight: 600,
                          fontSize: '0.625rem',
                          flexShrink: 0,
                        }}
                      >
                        {src.document_type || 'REFERENCE'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Metadata Footer: Timestamp, Model badge & RAG badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: isUser ? 'flex-end' : 'flex-start',
              gap: '0.5rem',
              padding: '0 0.25rem',
              fontSize: '0.6875rem',
              color: 'var(--secondary-500)',
            }}
          >
            {formattedTime && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Clock size={11} /> {formattedTime}
              </span>
            )}
            {!isUser && message.model_name && (
              <span
                style={{
                  background: 'var(--secondary-100)',
                  color: 'var(--secondary-700)',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  fontWeight: 600,
                  fontSize: '0.625rem',
                }}
              >
                {message.model_name}
              </span>
            )}
            {ragUsed && (
              <span
                style={{
                  background: '#f0fdfa',
                  color: 'var(--primary-700)',
                  border: '1px solid #ccfbf1',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  fontWeight: 600,
                  fontSize: '0.625rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                }}
              >
                <ShieldCheck size={10} color="var(--primary-600)" />
                Knowledge Base
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
