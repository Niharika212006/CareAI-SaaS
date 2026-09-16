import React, { useState, useEffect } from 'react';
import { Key, Sparkles, CheckCircle2, AlertCircle, X, ExternalLink, ShieldCheck, Cpu } from 'lucide-react';
import aiAssistantService from '../../services/aiAssistantService';
import Button from '../common/Button';

export function AIKeyModal({ isOpen, onClose, onConfigUpdated }) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [config, setConfig] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch current AI configuration on open
  useEffect(() => {
    if (!isOpen) return;
    setStatusMessage(null);
    setErrorMessage(null);

    async function loadConfig() {
      try {
        setIsLoading(true);
        const res = await aiAssistantService.getConfig();
        setConfig(res);
      } catch (err) {
        console.error('Failed to load AI config:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadConfig();
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const res = await aiAssistantService.updateConfig(apiKey.trim());
      setConfig(res.config);
      setStatusMessage(res.message || 'AI configuration successfully updated!');
      setApiKey('');
      if (onConfigUpdated) {
        onConfigUpdated(res.config);
      }
    } catch (err) {
      console.error('Failed to update Gemini API key:', err);
      setErrorMessage(err.message || 'Failed to update Gemini API key. Please check your network or key.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearKey = async () => {
    setIsSaving(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const res = await aiAssistantService.updateConfig('');
      setConfig(res.config);
      setStatusMessage('Reset to local CareAI Clinical Intelligence Engine.');
      setApiKey('');
      if (onConfigUpdated) {
        onConfigUpdated(res.config);
      }
    } catch (err) {
      console.error('Failed to clear key:', err);
      setErrorMessage(err.message || 'Failed to reset key.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          background: '#ffffff',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '520px',
          padding: '1.75rem',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, var(--primary-600) 0%, var(--accent-blue) 100%)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 10px rgba(13, 148, 136, 0.3)',
              }}
            >
              <Key size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: 'var(--secondary-900)' }}>
                CareAI Intelligence Settings
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--secondary-500)', margin: '2px 0 0 0' }}>
                Manage live Google Gemini API integration
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="btn-icon-subtle"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--secondary-400)',
              padding: '4px',
              borderRadius: '8px',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Current Status Card */}
        <div
          style={{
            background: config?.has_live_credentials ? 'var(--success-50)' : 'var(--primary-50)',
            border: `1px solid ${config?.has_live_credentials ? 'var(--success-200)' : 'var(--primary-200)'}`,
            borderRadius: '12px',
            padding: '0.875rem 1rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            {config?.has_live_credentials ? (
              <Sparkles size={20} color="var(--success-600)" />
            ) : (
              <Cpu size={20} color="var(--primary-600)" />
            )}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--secondary-500)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Active AI Engine
              </div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--secondary-900)' }}>
                {config ? config.active_engine : 'Checking status...'}
              </div>
            </div>
          </div>

          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '3px 8px',
              borderRadius: '6px',
              background: config?.has_live_credentials ? 'var(--success-600)' : 'var(--primary-600)',
              color: '#ffffff',
            }}
          >
            {config?.has_live_credentials ? 'Live Gemini AI' : 'Clinical Engine'}
          </span>
        </div>

        {/* Feedback alerts */}
        {statusMessage && (
          <div
            style={{
              background: 'var(--success-50)',
              border: '1px solid var(--success-200)',
              color: 'var(--success-800)',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem',
            }}
          >
            <CheckCircle2 size={18} />
            <span>{statusMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div
            style={{
              background: '#fff1f2',
              border: '1px solid #fecdd3',
              color: '#be123c',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1rem',
            }}
          >
            <AlertCircle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSave}>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
              <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--secondary-800)' }}>
                Google Gemini API Key
              </label>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--primary-600)',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  textDecoration: 'none',
                }}
              >
                Get a free key <ExternalLink size={12} />
              </a>
            </div>

            <div style={{ position: 'relative' }}>
              <input
                type={showKey ? 'text' : 'password'}
                placeholder={config?.has_live_credentials ? '••••••••••••••••••••••••••••••••' : 'AIzaSy...'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={isSaving}
                className="form-input"
                style={{
                  width: '100%',
                  paddingRight: '4.5rem',
                  fontSize: '0.875rem',
                  fontFamily: apiKey ? 'monospace' : 'inherit',
                }}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                style={{
                  position: 'absolute',
                  right: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  fontSize: '0.75rem',
                  color: 'var(--secondary-500)',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: '4px 6px',
                }}
              >
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--secondary-500)', marginTop: '0.375rem' }}>
              Your API key is saved directly to your server environment and used strictly for generating real-time clinical responses.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1.5rem' }}>
            <Button
              type="submit"
              variant="primary"
              disabled={isSaving || !apiKey.trim()}
              style={{ flex: 1, padding: '0.625rem' }}
            >
              {isSaving ? 'Connecting...' : 'Activate Gemini AI'}
            </Button>

            {config?.has_live_credentials && (
              <Button
                type="button"
                variant="outline"
                onClick={handleClearKey}
                disabled={isSaving}
                style={{ padding: '0.625rem' }}
              >
                Clear Key
              </Button>
            )}

            <Button
              type="button"
              variant="subtle"
              onClick={onClose}
              disabled={isSaving}
              style={{ padding: '0.625rem' }}
            >
              Close
            </Button>
          </div>
        </form>

        {/* Note on Clinical Knowledge Engine */}
        <div
          style={{
            marginTop: '1.25rem',
            paddingTop: '1rem',
            borderTop: '1px solid var(--secondary-100)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.75rem',
            color: 'var(--secondary-500)',
          }}
        >
          <ShieldCheck size={16} color="var(--primary-600)" style={{ flexShrink: 0 }} />
          <span>
            Even without an external API key, CareAI uses the built-in Clinical Intelligence Engine to provide deep, medically accurate answers for all 5 roles.
          </span>
        </div>
      </div>
    </div>
  );
}

export default AIKeyModal;
