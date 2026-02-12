import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const InterviewPage = ({
  currentIdx,
  totalQuestions,
  question,
<<<<<<< HEAD
<<<<<<< HEAD
=======
  audioUrl,
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
  audioUrl,
>>>>>>> 린_phase4
  isRecording,
  transcript,
  toggleRecording,
  nextQuestion,
  onFinish,
  videoRef,
  isLoading
}) => {
  const [timeLeft, setTimeLeft] = React.useState(60);
  const [showTooltip, setShowTooltip] = React.useState(false);
<<<<<<< HEAD
<<<<<<< HEAD

  React.useEffect(() => {
    setTimeLeft(60); // 질문이 바뀔 때마다 60초로 리셋
  }, [currentIdx]);
=======
  const audioRef = React.useRef(null);

  React.useEffect(() => {
    setTimeLeft(60); // 질문이 바뀔 때마다 60초로 리셋
=======
  const audioRef = React.useRef(null);

  React.useEffect(() => {
    setTimeLeft(60); // 질문이 바뀔 때마다 60초로 리셋
>>>>>>> 린_phase4
    
    // TTS 재생 로직
    const playTTS = () => {
      // 1. 서버 제공 오디오 URL이 있는 경우
      if (audioUrl) {
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.play().catch(e => console.error("Audio play failed:", e));
      } 
      // 2. URL이 없으면 브라우저 내장 TTS 사용 (Fallback)
      else if (question) {
        if (window.speechSynthesis) {
          window.speechSynthesis.cancel(); // 이전 발화 중지
          const utterance = new SpeechSynthesisUtterance(question);
          utterance.lang = 'ko-KR';
          utterance.rate = 1.0; 
          utterance.pitch = 1.0;
          window.speechSynthesis.speak(utterance);
        }
      }
    };

    playTTS();

    // Cleanup: 컴포넌트 언마운트 시 오디오 중지
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [currentIdx, audioUrl, question]);
<<<<<<< HEAD
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
>>>>>>> 린_phase4

  React.useEffect(() => {
    // 타이머 기능 활성화
    if (timeLeft <= 0) {
      if (!isRecording) nextQuestion();
      return;
    }

<<<<<<< HEAD
=======
    // 타이머 설정
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
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
    <div className="interview-container animate-fade-in" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', paddingTop: '5rem', paddingBottom: '1rem', display: 'flex', flexDirection: 'column', height: '100vh', boxSizing: 'border-box', position: 'relative' }}>

      {/* Loading Overlay */}
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '20px',
          color: 'white'
        }}>
          <div className="spinner" style={{ marginBottom: '1.5rem', width: '50px', height: '50px', border: '4px solid rgba(255,255,255,0.1)', borderTop: '4px solid var(--primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <h3 style={{ fontSize: '1.5rem', fontWeight: '700' }}>AI 면접관이 다음 질문을 생각 중입니다...</h3>
          <p style={{ marginTop: '0.5rem', opacity: 0.8 }}>이력서 내용을 바탕으로 질문을 생성하고 있습니다. 잠시만 기다려주세요.</p>
          <style>{`
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
          `}</style>
        </div>
      )}

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
          <PremiumButton
            onClick={nextQuestion}
            style={{ flex: 1, minWidth: '140px', padding: '1rem', fontSize: '1rem', fontWeight: '700' }}
          >
            {currentIdx < totalQuestions - 1 ? '다음 질문' : '답변 제출'}
          </PremiumButton>
          <div style={{ position: 'relative', flex: 1, minWidth: '140px' }}>
            {showTooltip && (
              <div style={{
                position: 'absolute',
                bottom: '100%',
                left: '50%',
                transform: 'translate(-50%, -10px)',
                background: 'rgba(15, 23, 42, 0.95)',
                backdropFilter: 'blur(8px)',
                color: 'white',
                padding: '14px 18px',
                borderRadius: '12px',
                fontSize: '0.9rem',
                lineHeight: '1.6',
                textAlign: 'center',
                whiteSpace: 'pre-line',
                zIndex: 2000,
                width: 'max-content',
                maxWidth: '320px',
                boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.15)',
                pointerEvents: 'none',
                animation: 'tooltipFadeIn 0.3s ease-out forwards'
              }}>
                {"면접을 종료하면 결과를 확인할 수 없으며,\n동일한 면접에 대한 재응시는 어렵습니다.\n처음부터 다시 시작해야 하니 주의해 주세요."}
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  borderWidth: '8px',
                  borderStyle: 'solid',
                  borderColor: 'rgba(15, 23, 42, 0.95) transparent transparent transparent'
                }}></div>
              </div>
            )}
            <style>{`
              @keyframes tooltipFadeIn {
                from { opacity: 0; transform: translate(-50%, 0); }
                to { opacity: 1; transform: translate(-50%, -10px); }
              }
            `}</style>

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
