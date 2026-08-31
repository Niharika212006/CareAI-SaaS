import React from 'react';

export function Card({ children, title, subtitle, className = '', hover = false, headerAction }) {
  return (
    <div className={`card ${hover ? 'card-hover' : ''} ${className}`}>
      {(title || subtitle || headerAction) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
          <div>
            {title && <h3 style={{ fontSize: '1.125rem', marginBottom: '0.25rem' }}>{title}</h3>}
            {subtitle && <p style={{ fontSize: '0.875rem', color: 'var(--secondary-500)' }}>{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export default Card;
