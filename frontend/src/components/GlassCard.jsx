import React from 'react';

export default function GlassCard({ children, className = '', hover = false }) {
  return (
    <div
      className={`glass-panel rounded-2xl p-6 ${
        hover ? 'glass-panel-hover cursor-pointer' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}
