import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const FinalGuidePage = ({ onNext, onPrev, isLoading }) => {
  const isAudioOk = sessionStorage.getItem('env_audio_ok') === 'true';
  const isVideoOk = sessionStorage.getItem('env_video_ok') === 'true';
  const allPassed = isAudioOk && isVideoOk;

  const getStatusStyle = (isOk) => ({
    flex: 1,
    background: isOk ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
    backdropFilter: 'blur(10px)',
    border: `1px solid ${isOk ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'}`,
    borderRadius: '24px',
    padding: '1.5rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    transition: 'all 0.3s ease'
  });

  const getIconStyle = (isOk) => ({
    width: '50px', height: '50px', borderRadius: '50%',
    background: isOk ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: '1.5rem'
  });

  return (
    <div className="final-guide animate-fade-in" style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2rem',
      boxSizing: 'border-box'
    }}>
      <div className="content-wrapper" style={{
        maxWidth: '700px',
        width: '100%',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        gap: '2.5rem'
      }}>

        {/* Header */}
        <div className="header-section">
          <div className="logo-wrapper" style={{ width: '150px', marginBottom: '1.5rem', margin: '0 auto' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
          <h1 className="text-gradient" style={{ fontSize: '2.2rem', fontWeight: 'bold', marginBottom: '0.8rem' }}>
            {allPassed ? '환경 테스트 완료' : '환경 테스트 미완료'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
            {allPassed
              ? <><span>모든 준비가 완료되었습니다.<br />최상의 컨디션으로 면접을 시작해보세요.</span></>
              : <><span style={{ color: '#ef4444' }}>음성과 카메라 테스트를 모두 통과해야 면접을 시작할 수 있습니다.<br />재설정 버튼을 눌러 다시 테스트해주세요.</span></>
            }
          </p>
        </div>

        {/* Status Check Cards */}
        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
          {/* Audio Status */}
          <div style={getStatusStyle(isAudioOk)}>
            <div style={getIconStyle(isAudioOk)}>
              🎤
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>음성 입력</div>
              <div style={{ fontWeight: 'bold', color: isAudioOk ? '#10b981' : '#ef4444' }}>
                {isAudioOk ? '✓ 테스트 완료' : '✗ 테스트 실패'}
              </div>
            </div>
          </div>

          {/* Video Status */}
          <div style={getStatusStyle(isVideoOk)}>
            <div style={getIconStyle(isVideoOk)}>
              📷
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>영상 인식</div>
              <div style={{ fontWeight: 'bold', color: isVideoOk ? '#10b981' : '#ef4444' }}>
                {isVideoOk ? '✓ 테스트 완료' : '✗ 테스트 실패'}
              </div>
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <PremiumButton variant="secondary" onClick={onPrev} disabled={isLoading} style={{ flex: 0.4 }}>
            재설정
          </PremiumButton>
          <PremiumButton
            onClick={onNext}
            disabled={isLoading || !allPassed}
            style={{
              flex: 1,
              padding: '1.2rem',
              fontSize: '1.1rem',
              opacity: allPassed ? 1 : 0.4,
              cursor: allPassed ? 'pointer' : 'not-allowed'
            }}
          >
            {isLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <div className="spinner" style={{ width: '20px', height: '20px', margin: 0, borderTopColor: '#fff', borderRightColor: 'rgba(255,255,255,0.3)', borderBottomColor: 'rgba(255,255,255,0.3)', borderLeftColor: 'rgba(255,255,255,0.3)' }}></div>
                <span>면접실 입장 중...</span>
              </div>
            ) : allPassed ? '지금 면접 시작하기' : '테스트를 먼저 완료해주세요'}
          </PremiumButton>
        </div>
      </div>
    </div>
  );
};

export default FinalGuidePage;