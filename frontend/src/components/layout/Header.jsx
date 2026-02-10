import React from 'react';

const Header = ({ onLogout, showLogout = false, onLogoClick, isInterviewing = false, isComplete = false, onHistory, onAccountSettings, onProfileManagement, onLogin, onRegister, pageTitle }) => {
  const [isManageOpen, setIsManageOpen] = React.useState(false);
  const [isMyInfoOpen, setIsMyInfoOpen] = React.useState(false);

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
          <div className="logo-wrapper" style={{ width: '120px' }}>
            <img src="/logo.png" alt="Logo" className="theme-logo" />
          </div>
        </div>

        {pageTitle && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginLeft: '1.5rem',
            paddingLeft: '1.5rem',
            borderLeft: '1px solid var(--glass-border)'
          }}>
            <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>{pageTitle}</span>
          </div>
        )}

        {isInterviewing && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginLeft: '1.5rem',
            paddingLeft: '1.5rem',
            borderLeft: '1px solid var(--glass-border)'
          }}>
            <span style={{ color: '#ef4444', fontSize: '1.2rem' }}>▶</span>
            <span style={{ fontSize: '1.3rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>면접 진행중</span>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(239, 68, 68, 0.1)',
              padding: '4px 12px',
              borderRadius: '6px',
              border: '1px solid rgba(239, 68, 68, 0.2)'
            }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }} className="blink"></div>
              <span style={{ fontSize: '0.9rem', fontWeight: '900', color: '#ef4444' }}>LIVE</span>
            </div>
          </div>
        )}
      </div>

      {!showLogout && !isInterviewing && !isComplete && (
        <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
          <button
            onClick={onLogin}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: '1px solid var(--glass-border)',
              background: 'transparent',
              color: 'var(--text-main)',
              cursor: 'pointer',
              transition: 'all 0.3s',
              outline: 'none'
            }}
            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            로그인
          </button>
          <button
            onClick={onRegister}
            style={{
              padding: '8px 24px',
              borderRadius: '20px',
              border: 'none',
              background: 'var(--primary)',
              color: 'white',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s',
              outline: 'none',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            회원가입
          </button>
        </div>
      )}

      {showLogout && !isInterviewing && !isComplete && (
        <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>

          {/* 면접 관리 드롭다운 */}
          <div
            className="header-dropdown-container"
            style={{ position: 'relative' }}
            onMouseEnter={() => setIsManageOpen(true)}
            onMouseLeave={() => setIsManageOpen(false)}
          >
            <button
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '1px solid var(--glass-border)',
                background: isManageOpen ? 'rgba(255,255,255,0.1)' : 'transparent',
                color: 'var(--text-main)',
                cursor: 'pointer',
                transition: 'all 0.3s',
                outline: 'none'
              }}
            >
              면접 관리
            </button>
            {isManageOpen && (
              <div className="header-dropdown-menu" style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                width: '160px',
                marginTop: '4px',
                background: 'var(--glass-bg)',
                backdropFilter: 'blur(12px)',
                border: '1px solid var(--glass-border)',
                borderRadius: '12px',
                padding: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                animation: 'fadeIn 0.2s ease'
              }}>
                <button className="dropdown-item" onClick={onHistory}>면접 이력</button>
              </div>
            )}
          </div>

          {/* 내 정보 드롭다운 */}
          <div
            className="header-dropdown-container"
            style={{ position: 'relative' }}
            onMouseEnter={() => setIsMyInfoOpen(true)}
            onMouseLeave={() => setIsMyInfoOpen(false)}
          >
            <button
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: '1px solid var(--glass-border)',
                background: isMyInfoOpen ? 'rgba(255,255,255,0.1)' : 'transparent',
                color: 'var(--text-main)',
                cursor: 'pointer',
                transition: 'all 0.3s',
                outline: 'none'
              }}
            >
              내 정보
            </button>
            {isMyInfoOpen && (
              <div className="header-dropdown-menu" style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                width: '160px',
                marginTop: '4px',
                background: 'var(--glass-bg)',
                backdropFilter: 'blur(12px)',
                border: '1px solid var(--glass-border)',
                borderRadius: '12px',
                padding: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                animation: 'fadeIn 0.2s ease'
              }}>
                <button className="dropdown-item" onClick={onProfileManagement}>프로필 관리</button>
                <button className="dropdown-item" onClick={onAccountSettings}>계정 관리</button>
              </div>
            )}
          </div>

          <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)', margin: 'auto 0' }}></div>

          <button
            onClick={onLogout}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: '1px solid #ef4444',
              background: 'rgba(239, 68, 68, 0.1)',
              color: '#ef4444',
              cursor: 'pointer',
              transition: 'all 0.3s',
              outline: 'none'
            }}
            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
            onMouseOut={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
          >
            로그아웃
          </button>

          <style>{`
            @keyframes fadeIn {
              from { opacity: 0; transform: translateY(-10px); }
              to { opacity: 1; transform: translateY(0); }
            }
            .dropdown-item {
              padding: 10px 12px;
              border-radius: 8px;
              background: transparent;
              border: none;
              color: var(--text-main);
              text-align: left;
              cursor: pointer;
              transition: all 0.2s;
              font-size: 0.9rem;
              white-space: nowrap;
              outline: none;
            }
            .dropdown-item:hover {
              background: rgba(255, 255, 255, 0.1);
            }
          `}</style>
        </div>
      )}
    </header>
  );
};

export default Header;
