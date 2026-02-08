import React from 'react';

const GlassCard = ({ children, className = '', ...props }) => {
  return (
    <div 
      className={`premium-card animate-fade-in ${className}`} 
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard;
