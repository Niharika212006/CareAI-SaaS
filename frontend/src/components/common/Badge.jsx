import React from 'react';

export function Badge({ children, variant = 'teal', className = '' }) {
  const variantClass = `badge-${variant}`;
  return <span className={`badge ${variantClass} ${className}`}>{children}</span>;
}

export default Badge;
