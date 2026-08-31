import React, { useState, useRef, useEffect } from 'react';
import { Send, Shield, CornerDownLeft } from 'lucide-react';

export function ChatInput({ onSendMessage, isSending, placeholder = 'Ask CareAI a question...' }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (!isSending && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isSending]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!text.trim() || isSending) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChange = (e) => {
    setText(e.target.value);
    // Auto-adjust height up to 140px
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  };

  return (
    <div
      style={{
        borderTop: '1px solid var(--secondary-200)',
        background: '#ffffff',
        padding: '1rem 1.25rem 0.75rem 1.25rem',
        borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
      }}
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div
          style={{
            position: 'relative',
            display: 'flex',
            alignItems: 'flex-end',
            background: 'var(--bg-main)',
            border: '1px solid var(--secondary-200)',
            borderRadius: 'var(--radius-md)',
            padding: '0.5rem 0.75rem',
            transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
          }}
          className="chat-input-wrapper"
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={isSending}
            placeholder={isSending ? 'CareAI is generating response...' : placeholder}
            rows={1}
            maxLength={4000}
            style={{
              width: '100%',
              border: 'none',
              outline: 'none',
              background: 'transparent',
              resize: 'none',
              fontSize: '0.875rem',
              color: 'var(--secondary-900)',
              fontFamily: 'inherit',
              maxHeight: '140px',
              paddingRight: '3rem',
              lineHeight: 1.5,
            }}
          />

          <button
            type="submit"
            disabled={!text.trim() || isSending}
            style={{
              position: 'absolute',
              right: '8px',
              bottom: '6px',
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              background:
                !text.trim() || isSending
                  ? 'var(--secondary-200)'
                  : 'linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%)',
              color: !text.trim() || isSending ? 'var(--secondary-500)' : '#ffffff',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: !text.trim() || isSending ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease',
              boxShadow: !text.trim() || isSending ? 'none' : '0 2px 6px rgba(13, 148, 136, 0.3)',
            }}
            title="Send Message (Enter)"
          >
            <Send size={15} />
          </button>
        </div>

        {/* Footer Disclaimer & Helpers */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.6875rem',
            color: 'var(--secondary-500)',
            padding: '0 0.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Shield size={11} color="var(--primary-600)" />
            <span>CareAI provides informational assistance and does not replace professional medical advice.</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            <span>{text.length}/4000</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }} className="hide-mobile">
              <CornerDownLeft size={10} /> Enter to send
            </span>
          </div>
        </div>
      </form>
    </div>
  );
}

export default ChatInput;
