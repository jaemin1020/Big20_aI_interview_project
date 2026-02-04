import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const MainPage = ({ 
  onStartInterview, 
  onLogin, 
  onRegister 
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
      <div style={{ position: 'absolute', top: 0, right: 0, display: 'flex', gap: '1rem' }}>
        <PremiumButton variant="secondary" onClick={onLogin} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
          로그인
        </PremiumButton>
        <PremiumButton onClick={onRegister} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
          회원가입
        </PremiumButton>
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
            소개문구<br/>
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
