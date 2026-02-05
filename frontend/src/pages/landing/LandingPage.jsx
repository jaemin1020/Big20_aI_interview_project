import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const LandingPage = ({ 
  startInterview, 
  handleLogout 
}) => {
  return (
    <div className="landing-container animate-fade-in" style={{ 
      flex: 1, 
      display: 'flex', 
      flexDirection: 'column', 
      justifyContent: 'center', 
      alignItems: 'center',
      width: '100%'
    }}>
      <GlassCard style={{ textAlign: 'center', maxWidth: '800px', width: '100%' }}>
        <div style={{ marginBottom: '3rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-wrapper" style={{ width: '200px' }}>
              <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
            지금부터 모의면접을 시작합니다.
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', opacity: 0.8 }}>
            아래 안내사항을 확인해주세요
          </p>
        </div>

        <div style={{ 
          border: '1px solid var(--glass-border)', 
          borderRadius: '16px', 
          padding: '1.5rem', 
          textAlign: 'left', 
          marginBottom: '2.5rem',
          background: 'rgba(255, 255, 255, 0.03)'
        }}>
          <ul style={{ 
            margin: 0, 
            paddingLeft: '1.2rem', 
            color: 'var(--text-main)', 
            fontSize: '1rem', 
            lineHeight: '1.8',
            listStyleType: 'disc' 
          }}>
            <li>예상 소요시간 : 20분</li>
            <li>진행 방식 : 영상 또는 음성 응답</li>
            <li>중간 종료 가능</li>
          </ul>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <PremiumButton 
            onClick={() => startInterview()}
            style={{ padding: '16px 60px', fontSize: '1.2rem' }}
          >
            면접 시작
          </PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default LandingPage;
