import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const LandingPage = ({ 
  userName, 
  setUserName, 
  position, 
  setPosition, 
  startInterview, 
  handleLogout 
}) => {
  return (
    <div className="landing-container animate-fade-in">
      <GlassCard style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ marginBottom: '3rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-wrapper" style={{ width: '200px' }}>
              <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
            생성형 AI가 제공하는 실시간 모의 면접 서비스입니다.<br/>
            귀하의 이력서와 직무에 맞춘 최적화된 질문을 통해 실전 감각을 키워보세요.
          </p>
        </div>

        <div className="input-group" style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr', 
          gap: '1.5rem', 
          textAlign: 'left',
          marginBottom: '2.5rem' 
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.95rem', fontWeight: '500' }}>이름</label>
            <input 
              type="text" 
              placeholder="이름을 입력하세요" 
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '10px', fontSize: '0.95rem', fontWeight: '500' }}>지원 직무</label>
            <input 
              type="text" 
              placeholder="예: Backend 개발자" 
              value={position}
              onChange={(e) => setPosition(e.target.value)}
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem' }}>
          <PremiumButton 
            onClick={() => startInterview(userName, position)}
            style={{ padding: '16px 40px', fontSize: '1.1rem' }}
          >
            면접 시작하기
          </PremiumButton>
          <PremiumButton 
            variant="secondary"
            style={{ padding: '16px 40px', fontSize: '1.1rem' }}
          >
            더 알아보기
          </PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default LandingPage;
