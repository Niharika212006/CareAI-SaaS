import React from 'react';

export function Footer() {
  return (
    <footer
      style={{
        borderTop: '1px solid var(--secondary-200)',
        backgroundColor: '#ffffff',
        padding: '1.25rem 1.5rem',
        marginTop: 'auto',
      }}
    >
      <div
        className="page-container"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: 0,
          fontSize: '0.8125rem',
          color: 'var(--secondary-500)',
        }}
      >
        <div>
          © {new Date().getFullYear()} AI Healthcare SaaS Platform. Clinical & Decision Support System.
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <span>HIPAA-Ready Architecture</span>
          <span>•</span>
          <span>Role-Based Security</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
