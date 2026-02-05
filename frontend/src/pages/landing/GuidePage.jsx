import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const GuidePage = ({ onNext }) => {
  return (
    <div className="guide-container animate-fade-in">
      <GlassCard style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎙️</div>
        <h1 className="text-gradient">면접 시작</h1>
        <p style={{ fontSize: '1.2rem', marginBottom: '2rem' }}>
          지금부터 모의면접을 시작합니다.<br/>
          아래 안내사항을 확인해주세요.
        </p>

        <div className="glass-effect" style={{ 
          textAlign: 'left', 
          padding: '1.5rem', 
          marginBottom: '2rem',
          background: 'rgba(255, 255, 255, 0.05)'
        }}>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>•</span>
              예상 소요시간: 20분
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>•</span>
              진행 방식: 영상 또는 음성 응답
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>•</span>
              중간 종료 가능
            </li>
          </ul>
        </div>

        <PremiumButton onClick={onNext} style={{ width: '100%', padding: '16px' }}>
          확인했습니다 (면접 시작)
        </PremiumButton>
      </GlassCard>
    </div>
  );
};

export default GuidePage;
