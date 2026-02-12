import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const FinalGuidePage = ({ onNext, onPrev, isLoading }) => {
  const isAudioOk = sessionStorage.getItem('env_audio_ok') === 'true';
  // const isVideoOk = sessionStorage.getItem('env_video_ok') === 'true';
  const isVideoOk = true; // [임시] 얼굴 인식 체크 무시
  const allPassed = isAudioOk && isVideoOk;

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
            {allPassed ? "환경 테스트 완료" : "환경 테스트 실패"}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
            {allPassed
              ? <>모든 준비가 완료되었습니다.<br />최상의 컨디션으로 면접을 시작해보세요.</>
              : <>일부 장치의 테스트가 완료되지 않았습니다.<br />설정을 확인 후 다시 시도해주세요.</>
            }
          </p>
        </div>

        {/* Status Check Cards */}
        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
          {/* Audio Status */}
          <div style={{
            flex: 1,
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            border: '1px solid var(--glass-border)',
            borderRadius: '24px',
            padding: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <div style={{
              width: '50px', height: '50px', borderRadius: '50%',
              background: sessionStorage.getItem('env_audio_ok') === 'true' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.5rem'
            }}>
              {sessionStorage.getItem('env_audio_ok') === 'true' ? '🎤' : '🔇'}
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>음성 입력</div>
              <div style={{ fontWeight: 'bold', color: 'var(--text-main)' }}>
                {sessionStorage.getItem('env_audio_ok') === 'true' ? '테스트 완료' : '인식 실패'}
              </div>
            </div>
          </div>

          {/* Video Status */}
          <div style={{
            flex: 1,
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(10px)',
            border: '1px solid var(--glass-border)',
            borderRadius: '24px',
            padding: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <div style={{
              width: '50px', height: '50px', borderRadius: '50%',
              background: sessionStorage.getItem('env_video_ok') === 'true' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.5rem'
            }}>
              {sessionStorage.getItem('env_video_ok') === 'true' ? '📷' : '🚫'}
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>영상 인식</div>
              <div style={{ fontWeight: 'bold', color: 'var(--text-main)' }}>
                {sessionStorage.getItem('env_video_ok') === 'true' ? '테스트 완료' : '인식 실패'}
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
              opacity: allPassed ? 1 : 0.5,
              cursor: allPassed ? 'pointer' : 'not-allowed'
            }}
          >
            {isLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <div className="spinner" style={{ width: '20px', height: '20px', margin: 0, borderTopColor: '#fff', borderRightColor: 'rgba(255,255,255,0.3)', borderBottomColor: 'rgba(255,255,255,0.3)', borderLeftColor: 'rgba(255,255,255,0.3)' }}></div>
                <span>면접실 입장 중...</span>
              </div>
            ) : '지금 면접 시작하기'}
          </PremiumButton>
        </div>
      </div>
    </div>
  );
};

export default FinalGuidePage;