import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const InterviewPage = ({ 
  currentIdx, 
  totalQuestions, 
  question, 
  isRecording, 
  transcript, 
  toggleRecording, 
  nextQuestion, 
  videoRef 
}) => {
  return (
    <div className="interview-container animate-fade-in" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '2rem', alignItems: 'start' }}>
      <div style={{ position: 'sticky', top: '2rem' }}>
        <video 
          ref={videoRef} 
          autoPlay 
          playsInline 
          muted 
          style={{ width: '100%', borderRadius: '24px', background: '#000', border: '1px solid var(--glass-border)' }}
        />
        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <div style={{ padding: '8px 16px', borderRadius: '50px', background: 'rgba(255, 255, 255, 0.05)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isRecording ? '#ef4444' : '#10b981' }}></div>
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{isRecording ? 'LIVE RECORDING' : 'IDLE'}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <GlassCard>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
            <span style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '1.1rem' }}>Q{currentIdx + 1}.</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{currentIdx + 1} / {totalQuestions}</span>
          </div>
          <h2 style={{ fontSize: '1.8rem', lineHeight: '1.4', marginBottom: '2rem' }}>{question}</h2>

          <div className="transcript-box" style={{ 
            minHeight: '150px', 
            background: 'rgba(255, 255, 255, 0.03)', 
            borderRadius: '16px', 
            padding: '1.5rem',
            border: '1px solid var(--glass-border)',
            position: 'relative'
          }}>
            <h4 style={{ color: isRecording ? '#ef4444' : 'var(--text-muted)', marginBottom: '1rem', fontSize: '0.85rem' }}>
              {isRecording ? '🎤 실시간 인식 중...' : '마이크가 대기 중입니다.'}
            </h4>
            <p style={{ margin: 0, fontSize: '1.1rem', color: transcript ? 'var(--text-main)' : 'var(--text-muted)' }}>
              {transcript || '답변을 시작하려면 아래 녹음 버튼을 눌러주세요.'}
            </p>
          </div>
        </GlassCard>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <PremiumButton 
            variant={isRecording ? 'danger' : 'success'} 
            onClick={toggleRecording}
            style={{ flex: 1, padding: '1.2rem' }}
          >
            {isRecording ? '⏸ 답변 종료' : '🎤 답변 시작'}
          </PremiumButton>
          <PremiumButton 
            onClick={nextQuestion} 
            disabled={!transcript && !isRecording}
            style={{ flex: 1, padding: '1.2rem' }}
          >
            {currentIdx < totalQuestions - 1 ? '다음 질문 ➡️' : '면접 종료 ✓'}
          </PremiumButton>
        </div>
      </div>
    </div>
  );
};

export default InterviewPage;
