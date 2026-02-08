import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const FinalGuidePage = ({ onNext, onPrev, isLoading }) => {
  return (
    <div className="final-guide animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%' }}>
      <GlassCard style={{ maxWidth: '600px', width: '100%', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-wrapper" style={{ width: '180px' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
        </div>
        <h1 className="text-gradient">환경 테스트 완료</h1>
        <p style={{ marginBottom: '2rem' }}>모든 준비가 완료되었습니다. 이제 면접을 시작합니다.</p>

        <div style={{ 
          background: 'rgba(255, 255, 255, 0.03)', 
          padding: '2rem', 
          borderRadius: '16px', 
          marginBottom: '2rem',
          border: '1px solid var(--glass-border)'
        }}>
          <div style={{ color: 'var(--text-main)', fontSize: '1.2rem', fontWeight: '600', marginBottom: '1rem' }}>
            ✅ 면접 준비가 완료되었습니다.
          </div>
          <ul style={{ textAlign: 'left', listStyle: 'none', padding: 0, margin: 0, color: 'var(--text-muted)' }}>
            <li style={{ marginBottom: '8px' }}>• 음성 입력 정상</li>
            <li style={{ marginBottom: '8px' }}>• 영상 인식 정상</li>
          </ul>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <PremiumButton onClick={onNext} disabled={isLoading} style={{ flex: 1, padding: '16px' }}>
            {isLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <div className="spinner" style={{ width: '20px', height: '20px', margin: 0 }}></div>
                <span>준비 중...</span>
              </div>
            ) : '면접 시작'}
          </PremiumButton>
          <PremiumButton variant="secondary" onClick={onPrev} disabled={isLoading}>이전 단계</PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default FinalGuidePage;
