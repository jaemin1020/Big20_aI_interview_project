import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const MainPage = ({
  onStartInterview,
  onLogin,
  onRegister,
  user,
  onLogout,
  onHistory
}) => {
  return (
    <div className="main-container animate-fade-in" style={{
      flex: 1,
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      position: 'relative',
      padding: '2rem 0'
    }}>
      {/* Auth Buttons - Absolute Position Top Right */}
      <div style={{ position: 'absolute', top: 0, right: 0, display: 'flex', gap: '1rem', alignItems: 'center', zIndex: 100 }}>
        {user ? (
          <>
            {/* 면접 관리 드롭다운 */}
            <div className="dropdown-container" style={{ position: 'relative' }}>
              <PremiumButton
                variant="secondary"
                style={{ padding: '8px 20px', fontSize: '0.9rem' }}
              >
                면접 관리
              </PremiumButton>
              <div className="dropdown-menu" style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                width: '160px',
                marginTop: '8px',
                background: 'var(--glass-bg)',
                backdropFilter: 'blur(12px)',
                border: '1px solid var(--glass-border)',
                borderRadius: '12px',
                padding: '8px',
                display: 'none', // CSS로 호버 처리 (스타일 태그 필요) 또는 JS로 처리
                flexDirection: 'column',
                gap: '4px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
              }}>
                <button className="dropdown-item" onClick={onHistory}>면접 이력</button>
              </div>
            </div>

            {/* 내 정보 드롭다운 */}
            <div className="dropdown-container" style={{ position: 'relative' }}>
              <PremiumButton
                variant="secondary"
                style={{ padding: '8px 20px', fontSize: '0.9rem' }}
              >
                내 정보
              </PremiumButton>
              <div className="dropdown-menu" style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                width: '160px',
                marginTop: '8px',
                background: 'var(--glass-bg)',
                backdropFilter: 'blur(12px)',
                border: '1px solid var(--glass-border)',
                borderRadius: '12px',
                padding: '8px',
                display: 'none',
                flexDirection: 'column',
                gap: '4px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
              }}>
                <button className="dropdown-item" onClick={() => alert("준비 중인 기능입니다.")}>프로필 관리</button>
                <button className="dropdown-item" onClick={() => alert("준비 중인 기능입니다.")}>계정 관리</button>
              </div>
            </div>

            <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>

            <PremiumButton
              variant="secondary"
              onClick={onLogout}
              style={{
                padding: '8px 20px',
                fontSize: '0.9rem',
                color: '#ef4444',
                borderColor: '#ef4444',
                background: 'rgba(239, 68, 68, 0.05)'
              }}
            >
              로그아웃
            </PremiumButton>

            {/* Inline CSS for Hover Effect (임시) */}
            <style>{`
              .dropdown-container:hover .dropdown-menu {
                display: flex !important;
                animation: fadeIn 0.2s ease;
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
              }
              .dropdown-item:hover {
                background: rgba(255, 255, 255, 0.1);
              }
              @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
              }
            `}</style>
          </>
        ) : (
          <>
            <PremiumButton variant="secondary" onClick={onLogin} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
              로그인
            </PremiumButton>
            <PremiumButton onClick={onRegister} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
              회원가입
            </PremiumButton>
          </>
        )}
      </div>

      <div style={{ textAlign: 'center', padding: '4rem 3rem', maxWidth: '800px' }}>
        {/* Step 1: Branding */}
        <div style={{ marginBottom: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div className="logo-wrapper" style={{ width: '320px', marginBottom: '1rem' }}>
            <img
              src="/logo.png"
              alt="BIGVIEW Logo"
              className="theme-logo"
            />
          </div>
        </div>

        {/* Step 2: Welcome Message */}
        <div style={{ marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: '600', marginBottom: '1rem', opacity: 0.9 }}>
            환영합니다!
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem', lineHeight: '1.8' }}>
            소개문구<br />
          </p>
        </div>

        {/* Step 3, 4: Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem' }}>
          <PremiumButton
            onClick={onStartInterview}
            style={{ padding: '18px 48px', fontSize: '1.2rem' }}
          >
            면접 시작
          </PremiumButton>
          <PremiumButton
            variant="secondary"
            style={{ padding: '18px 48px', fontSize: '1.2rem' }}
          >
            더 알아보기
          </PremiumButton>
        </div>
      </div>

      {/* Decorative Blur Circles */}
      <div style={{
        position: 'absolute',
        top: '10%',
        left: '5%',
        width: '300px',
        height: '300px',
        background: 'var(--primary)',
        filter: 'blur(150px)',
        opacity: 0.15,
        zIndex: -1
      }}></div>
      <div style={{
        position: 'absolute',
        bottom: '10%',
        right: '5%',
        width: '300px',
        height: '300px',
        background: 'var(--secondary)',
        filter: 'blur(150px)',
        opacity: 0.1,
        zIndex: -1
      }}></div>
    </div>
  );
};

export default MainPage;
