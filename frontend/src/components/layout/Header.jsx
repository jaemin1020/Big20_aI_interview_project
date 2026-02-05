import React from 'react';

const Header = ({ onLogout, showLogout = false, onLogoClick }) => {
  return (
    <header style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      padding: '0.6rem 2rem',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 1000,
    }}>
      <div 
        onClick={onLogoClick} 
        style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', cursor: 'pointer' }}
      >
        <div className="logo-wrapper" style={{ width: '32px' }}>
          <img src="/logo.png" alt="Logo" className="theme-logo" />
        </div>
        <span style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--primary)', letterSpacing: '0.1em' }}>BIGVIEW</span>
      </div>
      
      {showLogout && (
        <button 
          onClick={onLogout}
          style={{ 
            padding: '8px 16px', 
            borderRadius: '20px', 
            border: '1px solid var(--glass-border)', 
            background: 'transparent',
            color: 'var(--text-main)',
            cursor: 'pointer',
            transition: 'all 0.3s'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
        >
          로그아웃
        </button>
      )}
    </header>
  );
};

export default Header;
