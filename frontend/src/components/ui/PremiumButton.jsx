import React from 'react';

const PremiumButton = ({
  children,
  variant = 'primary',
  className = '',
  as: Component = 'button',
  ...props
}) => {
  const baseStyles = {
    borderRadius: '50px',
    border: 'none',
    padding: '14px 28px',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    color: 'white',
    boxShadow: 'none', // CSS에서 제어
  };

  const variants = {
    primary: {
      background: 'linear-gradient(135deg, var(--primary) 0%, hsl(var(--primary-h), var(--primary-s), 40%) 100%)',
    },
    secondary: {
      background: 'var(--glass-bg)',
      backdropFilter: 'blur(12px)',
      border: '1px solid var(--glass-border)',
      color: 'var(--text-main)',
    },
    danger: {
      background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
    },
    success: {
      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    }
  };

  const { style: propsStyle, ...otherProps } = props;
  const combinedStyle = { ...baseStyles, ...variants[variant], ...propsStyle };

  return (
    <Component
      style={combinedStyle}
      className={`premium-button ${className}`}
      {...otherProps}
    >
      {children}
    </Component>
  );
};

export default PremiumButton;
