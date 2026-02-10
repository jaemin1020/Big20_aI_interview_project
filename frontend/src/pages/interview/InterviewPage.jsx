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
  onFinish,
  videoRef
}) => {
  const [timeLeft, setTimeLeft] = React.useState(60);
  const [showTooltip, setShowTooltip] = React.useState(false);

  React.useEffect(() => {
    setTimeLeft(60); // 질문이 바뀔 때마다 60초로 리셋
  }, [currentIdx]);

  React.useEffect(() => {
    // 타이머 기능 활성화
    if (timeLeft <= 0) {
      if (!isRecording) nextQuestion();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, nextQuestion, isRecording]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  return (
    <div className="interview-container animate-fade-in" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', paddingTop: '1rem', paddingBottom: '1rem', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)', boxSizing: 'border-box', overflow: 'hidden' }}>

      {/* Rectangular Timer Box: White background with Icon */}
      <div style={{
        alignSelf: 'flex-end',
        marginBottom: '0.5rem',
        padding: '6px 16px',
        background: '#ffffff',
        border: '1px solid rgba(0,0,0,0.05)',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        zIndex: 10
      }}>
        <span style={{ fontSize: '1rem' }} className={timeLeft <= 10 ? 'blink' : ''}>⏱️</span>
        <span style={{
          fontSize: '1.2rem',
          fontWeight: '800',
          fontFamily: "'Inter', monospace",
          color: timeLeft <= 10 ? '#ef4444' : '#0f172a',
          letterSpacing: '0.05em'
        }}>
          {formatTime(timeLeft)}
        </span>
      </div>

      {/* Header Card: Question & Video Only */}
      <GlassCard style={{ padding: '1rem 2rem', marginBottom: '0.5rem', flexShrink: 0 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '2rem', alignItems: 'center' }}>

          {/* Left: Question Area */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '1rem' }}>
              <span style={{
                background: 'var(--primary)',
                color: 'white',
                padding: '2px 10px',
                borderRadius: '6px',
                fontWeight: '700',
                fontSize: '0.9rem'
              }}>Q{currentIdx + 1}</span>
            </div>

            <h2 style={{
              fontSize: '1.3rem',
              lineHeight: '1.4',
              margin: 0,
              color: 'var(--text-main)',
              wordBreak: 'keep-all'
            }}>
              {question}
            </h2>
          </div>

          {/* Right: Video Area */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', borderRadius: '20px', overflow: 'hidden', border: '1px solid var(--glass-border)', background: '#000' }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain' }}
              />
              <div style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                padding: '6px 14px',
                borderRadius: '50px',
                background: 'rgba(0,0,0,0.6)',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                border: '1px solid rgba(255,255,255,0.2)'
              }}>
                <div style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: isRecording ? '#ef4444' : '#10b981',
                  boxShadow: isRecording ? '0 0 8px #ef4444' : 'none'
                }}></div>
                <span style={{ fontSize: '0.9rem', fontWeight: '800', color: 'white', letterSpacing: '0.05em' }}>
                  {isRecording ? 'LIVE REC' : 'READY'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Bottom Area: Transcript & Controls */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, minHeight: 0 }}>

        {/* Transcript Box */}
        <div className="transcript-container" style={{
          flex: 1,
          minHeight: '100px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '20px',
          padding: '1.2rem 2rem',
          border: '1px solid var(--glass-border)',
          position: 'relative',
          overflowY: 'auto'
        }}>
          <h4 style={{
            color: isRecording ? '#ef4444' : 'var(--text-muted)',
            marginBottom: '0.8rem',
            fontSize: '0.8rem',
            fontWeight: '600',
            textTransform: 'uppercase'
          }}>
            {isRecording ? '🎤 실시간 인식 중...' : '답변 대기 중'}
          </h4>
          <p style={{
            margin: 0,
            fontSize: '1.1rem',
            lineHeight: '1.5',
            color: transcript ? 'var(--text-main)' : 'var(--text-muted)',
          }}>
            {transcript || '답변을 시작하려면 아래 녹음 버튼을 눌러주세요.'}
          </p>
        </div>

        {/* Status Indicator */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          padding: '0 0.5rem'
        }}>
          <div style={{
            padding: '6px 16px',
            borderRadius: '20px',
            background: isRecording ? 'rgba(239, 68, 68, 0.1)' : (transcript ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.05)'),
            border: isRecording ? '1px solid rgba(239, 68, 68, 0.2)' : (transcript ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid var(--glass-border)'),
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s ease'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isRecording ? '#ef4444' : (transcript ? '#10b981' : 'var(--text-muted)'),
              boxShadow: isRecording ? '0 0 8px #ef4444' : 'none',
              animation: isRecording ? 'pulse 1.5s infinite' : 'none'
            }}></div>
            <span style={{
              fontSize: '0.85rem',
              fontWeight: '700',
              color: isRecording ? '#ef4444' : (transcript ? '#10b981' : 'var(--text-muted)')
            }}>
              {isRecording ? '답변 수집 중...' : (transcript ? '답변 완료' : '답변 대기 중')}
            </span>
          </div>
          <style>{`
            @keyframes pulse {
              0% { opacity: 1; transform: scale(1); }
              50% { opacity: 0.5; transform: scale(1.2); }
              100% { opacity: 1; transform: scale(1); }
            }
          `}</style>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '0.8rem', justifyContent: 'center', paddingBottom: '1rem' }}>
          <PremiumButton
            variant={isRecording ? 'danger' : 'success'}
            onClick={toggleRecording}
            style={{ flex: 1, minWidth: '140px', padding: '1rem', fontSize: '1rem', fontWeight: '700' }}
          >
            {isRecording ? '⏸ 답변 종료' : '답변 시작'}
          </PremiumButton>
          {currentIdx < totalQuestions - 1 && (
            <PremiumButton
              onClick={nextQuestion}
              style={{ flex: 1, minWidth: '140px', padding: '1rem', fontSize: '1rem', fontWeight: '700' }}
            >
              다음 질문
            </PremiumButton>
          )}
          <div style={{ position: 'relative', flex: 1, minWidth: '140px' }}>
            {showTooltip && (
              <div className="animate-fade-in" style={{
                position: 'absolute',
                bottom: '100%',
                left: '50%',
                transform: 'translate(-50%, -10px)',
                background: 'rgba(0, 0, 0, 0.9)',
                backdropFilter: 'blur(4px)',
                color: 'white',
                padding: '12px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                lineHeight: '1.4',
                textAlign: 'center',
                whiteSpace: 'pre-line',
                zIndex: 100,
                width: 'max-content',
                maxWidth: '300px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                border: '1px solid rgba(255,255,255,0.1)',
                pointerEvents: 'none'
              }}>
                면접을 종료하면 결과를 확인 수 없으며,
                동일한 면접에 대한 재응시는 어렵습니다.
                면접을 다시 진행하려면 처음부터 다시 시작해야 합니다.
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  borderWidth: '6px',
                  borderStyle: 'solid',
                  borderColor: 'rgba(0, 0, 0, 0.9) transparent transparent transparent'
                }}></div>
              </div>
            )}
            <PremiumButton
              variant="secondary"
              onClick={onFinish}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              style={{ width: '100%', padding: '1rem', fontSize: '1rem', fontWeight: '700', border: '1px solid var(--glass-border)' }}
            >
              면접 종료
            </PremiumButton>
          </div>
        </div>
      </div>

    </div>
  );
};

export default InterviewPage;
