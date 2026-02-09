import React from 'react';

const Header = ({ onLogout, showLogout = false, onLogoClick, isInterviewing = false, isComplete = false }) => {
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
      background: (isInterviewing || isComplete) ? 'rgba(0, 0, 0, 0.2)' : 'transparent',
      backdropFilter: 'blur(10px)',
      borderBottom: (isInterviewing || isComplete) ? '1px solid var(--glass-border)' : 'none'
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div 
          onClick={onLogoClick} 
          style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
        >
          <div className="logo-wrapper" style={{ width: '32px' }}>
            <img src="/logo.png" alt="Logo" className="theme-logo" />
          </div>
        </div>

        {isInterviewing && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px', 
            marginLeft: '1.5rem', 
            paddingLeft: '1.5rem', 
            borderLeft: '1px solid var(--glass-border)' 
          }}>
            <span style={{ color: '#ef4444', fontSize: '0.8rem' }}>▶</span>
            <span style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>면접 진행중</span>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: 'rgba(239, 68, 68, 0.1)', 
              padding: '2px 10px', 
              borderRadius: '6px',
              border: '1px solid rgba(239, 68, 68, 0.2)'
            }}>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ef4444' }} className="blink"></div>
              <span style={{ fontSize: '0.7rem', fontWeight: '900', color: '#ef4444' }}>LIVE</span>
            </div>
          </div>
        )}

        {isComplete && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px', 
            marginLeft: '1.5rem', 
            paddingLeft: '1.5rem', 
            borderLeft: '1px solid var(--glass-border)' 
          }}>
            <span style={{ 
              color: '#64748b', 
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '14px',
              height: '14px',
              background: '#64748b',
              borderRadius: '2px'
            }}></span>
            <span style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>면접종료</span>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px', 
              background: 'rgba(100, 116, 139, 0.1)', 
              padding: '2px 10px', 
              borderRadius: '6px',
              border: '1px solid rgba(100, 116, 139, 0.2)'
            }}>
              <span style={{ fontSize: '0.7rem', fontWeight: '900', color: '#64748b' }}>CLOSED</span>
            </div>
          </div>
        )}
      </div>
      
      {showLogout && !isInterviewing && !isComplete && (
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
