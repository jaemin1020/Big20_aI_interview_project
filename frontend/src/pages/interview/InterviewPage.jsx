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

  React.useEffect(() => {
    setTimeLeft(60); // 질문이 바뀔 때마다 60초로 리셋
  }, [currentIdx]);

  React.useEffect(() => {
    // 타이머 기능 일시 중지 (사용자 요청)
    /*
    if (timeLeft <= 0) {
      if (!isRecording) nextQuestion();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
    */
  }, [timeLeft, nextQuestion, isRecording]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  return (
    <div className="interview-container animate-fade-in" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', paddingTop: '5rem', paddingBottom: '1rem', display: 'flex', flexDirection: 'column', height: '100vh', boxSizing: 'border-box' }}>

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
      <GlassCard style={{ padding: '1.5rem 2rem', marginBottom: '1rem' }}>
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
            <div style={{ position: 'relative', width: '100%', paddingTop: '75%', borderRadius: '20px', overflow: 'hidden', border: '1px solid var(--glass-border)', background: '#000' }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
              />
              <div style={{
                position: 'absolute',
                top: '0.8rem',
                right: '0.8rem',
                padding: '4px 10px',
                borderRadius: '50px',
                background: 'rgba(0,0,0,0.5)',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                border: '1px solid rgba(255,255,255,0.1)'
              }}>
                <div style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: isRecording ? '#ef4444' : '#10b981',
                }}></div>
                <span style={{ fontSize: '0.7rem', fontWeight: '700', color: 'white' }}>
                  {isRecording ? 'REC' : 'IDLE'}
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
          <PremiumButton
            variant="secondary"
            onClick={onFinish}
            style={{ flex: 1, minWidth: '140px', padding: '1rem', fontSize: '1rem', fontWeight: '700', border: '1px solid var(--glass-border)' }}
          >
            면접 종료
          </PremiumButton>
        </div>
      </div>

    </div>
  );
};

export default InterviewPage;
