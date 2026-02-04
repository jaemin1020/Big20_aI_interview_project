import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const FinalGuidePage = ({ onNext, onPrev }) => {
  return (
    <div className="final-guide animate-fade-in">
      <GlassCard style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h1 className="text-gradient">환경 테스트 완료</h1>
        <p style={{ marginBottom: '2rem' }}>모든 준비가 완료되었습니다. 이제 본격적으로 면접을 시작합니다.</p>

        <div style={{ 
          background: 'rgba(16, 185, 129, 0.1)', 
          padding: '2rem', 
          borderRadius: '16px', 
          marginBottom: '2rem',
          border: '1px solid var(--secondary)'
        }}>
          <div style={{ color: 'var(--secondary)', fontSize: '1.2rem', fontWeight: '600', marginBottom: '1rem' }}>
            ✅ 면접 준비가 완료되었습니다.
          </div>
          <ul style={{ textAlign: 'left', listStyle: 'none', padding: 0, margin: 0, color: 'rgba(255,255,255,0.8)' }}>
            <li style={{ marginBottom: '8px' }}>• 네트워크 상태 양호</li>
            <li style={{ marginBottom: '8px' }}>• 오디오 입력 정상</li>
            <li>• 카메라 인식 정상</li>
          </ul>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <PremiumButton onClick={onNext} style={{ flex: 1, padding: '16px' }}>면접 시작</PremiumButton>
          <PremiumButton variant="secondary" onClick={onPrev}>이전 단계</PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default FinalGuidePage;
