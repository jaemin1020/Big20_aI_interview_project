import React from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const InterviewPage = ({
  currentIdx,
  totalQuestions,
  question,
  audioUrl,
  isRecording,
  transcript,
  setTranscript,
  toggleRecording,
  nextQuestion,
  onFinish,
  videoRef,
  isLoading,
  isMediaReady,
  visionData // [NEW] Receive vision data
}) => {
  const [timeLeft, setTimeLeft] = React.useState(60);
  // isTimerActive는 ttsFinished state로 대체됨 (아래 54행)
  const [showTooltip, setShowTooltip] = React.useState(false);
  // 이전 질문 인덱스를 추적하여 질문 변경 시 상태를 즉시 리셋 (Stale State 방지)
  const [prevIdx, setPrevIdx] = React.useState(currentIdx);

  const audioRef = React.useRef(null);
  const isTimeOverRef = React.useRef(false); // 타이머 종료 처리 중복 방지용 Ref

  // audioUrl/question을 ref로 항상 최신값 유지 (stale closure 방지)
  const audioUrlRef = React.useRef(audioUrl);
  const questionRef = React.useRef(question);
  React.useEffect(() => { audioUrlRef.current = audioUrl; }, [audioUrl]);
  React.useEffect(() => { questionRef.current = question; }, [question]);

  // 데이터 전송 테스트: transcript와 isRecording 변경 감지
  React.useEffect(() => {
    console.log('[InterviewPage] Props updated:', {
      isRecording,
      transcript,
      transcriptLength: transcript?.length || 0,
      currentQuestion: question?.substring(0, 50)
    });
  }, [isRecording, transcript]);

  // 질문이 변경되면 렌더링 도중 즉시 상태 리셋
  if (currentIdx !== prevIdx) {
    setPrevIdx(currentIdx);
    setTimeLeft(60);
    // ttsFinished는 useEffect([currentIdx])에서 리셋됨
    isTimeOverRef.current = false;
  }

  // TTS 재생 완료 여부 — true가 되면 타이머 카운트다운 시작
  const [ttsFinished, setTtsFinished] = React.useState(false);
  const playedUrlRef = React.useRef(null);

  // 질문 인덱스가 바뀌면 모든 상태 리셋
  React.useEffect(() => {
    console.log(`🔄 [Question Change] Index: ${currentIdx}`);
    playedUrlRef.current = null;
    setTtsFinished(false);
    setTimeLeft(60);

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.onended = null;
        audioRef.current.onerror = null;
        audioRef.current = null;
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [currentIdx]);

  // audioUrl이 도착하면 재생
  React.useEffect(() => {
    if (!audioUrl || !question) return;

    const stripQuery = (url) => url?.split('?')[0] || '';
    const baseUrl = stripQuery(audioUrl);
    const playedBaseUrl = stripQuery(playedUrlRef.current);

    if (playedBaseUrl === baseUrl) return;

    console.log(`🔊 [TTS Play] Index: ${currentIdx}, URL: ${baseUrl}`);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current = null;
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    playedUrlRef.current = audioUrl;

    audio.onended = () => {
      // 현재 활성 오디오인지 확인 (stale 콜백 방지)
      if (audioRef.current !== audio) {
        console.warn("⚠️ [TTS] onended fired for stale audio, ignoring");
        return;
      }
      console.log("✅ [TTS] Audio ENDED → setTtsFinished(true)");
      setTtsFinished(true);
    };

    audio.onerror = (e) => {
      if (audioRef.current !== audio) {
        console.warn("⚠️ [TTS] onerror fired for stale audio, ignoring");
        return;
      }
      console.error("❌ [TTS] Audio ERROR → setTtsFinished(true)", e);
      setTtsFinished(true);
    };

    audio.play().then(() => {
      console.log("▶️ [TTS] 재생 시작됨. duration:", audio.duration);
    }).catch(e => {
      if (audioRef.current !== audio) return;
      console.error("❌ [TTS] play() 실패 → setTtsFinished(true)", e);
      setTtsFinished(true);
    });
  }, [audioUrl, currentIdx, question]);

  // 1분 카운트다운 — ttsFinished가 true일 때만 작동
  React.useEffect(() => {
    if (!ttsFinished) return; // ★ TTS 안 끝났으면 interval 안 만듦

    if (timeLeft <= 0) {
      if (isTimeOverRef.current) return;
      if (!isRecording) {
        console.log("⏰ Time over!");
      }
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, nextQuestion, isRecording, ttsFinished]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 진행률 계산
  const progressPercent = ((currentIdx + 1) / totalQuestions) * 100;

  return (
    <div className="interview-container animate-fade-in" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', paddingTop: '5rem', paddingBottom: '1rem', display: 'flex', flexDirection: 'column', height: '100vh', boxSizing: 'border-box', position: 'relative' }}>

      {/* Loading Overlay */}
      {
        isLoading && (
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
        )
      }

      {/* Progress Bar & Timer Container */}
      <div style={{ alignSelf: 'stretch', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>

        {/* Progress Bar */}
        <div style={{ flex: 1, marginRight: '2rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>
            <span>면접 진행률</span>
            <span>{Math.round(progressPercent)}% ({currentIdx + 1}/{totalQuestions})</span>
          </div>
          <div style={{ display: 'flex', width: '100%', height: '8px', gap: '6px' }}>
            {Array.from({ length: totalQuestions }).map((_, idx) => (
              <div key={idx} style={{
                flex: 1,
                height: '100%',
                background: idx <= currentIdx ? 'var(--primary)' : 'rgba(0,0,0,0.1)',
                borderRadius: '4px',
                transition: 'background 0.4s ease-out',
                boxShadow: idx <= currentIdx ? '0 0 8px rgba(var(--primary-rgb), 0.4)' : 'none'
              }}></div>
            ))}
          </div>
        </div>

        {/* Rectangular Timer Box */}
        <div style={{
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
          <span style={{ fontSize: '1rem' }} className={timeLeft <= 10 ? 'blink' : ''}>
            {ttsFinished ? '⏱️' : '🔇'}
          </span>
          <span style={{
            fontSize: '1.2rem',
            fontWeight: '800',
            fontFamily: "'Inter', monospace",
            color: timeLeft <= 10 ? '#ef4444' : '#0f172a',
            letterSpacing: '0.05em',
            opacity: ttsFinished ? 1 : 0.5
          }}>
            {formatTime(timeLeft)}
          </span>
        </div>
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

              {/* [추가] 면접 단계 배지 표시 */}
              {question?.startsWith('[') && question.includes(']') && (
                <span style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'var(--primary)',
                  padding: '2px 10px',
                  borderRadius: '6px',
                  fontWeight: '700',
                  fontSize: '0.9rem',
                  border: '1px solid var(--primary)'
                }}>
                  {question.split(']')[0].substring(1)}
                </span>
              )}
            </div>

            <h2 style={{
              fontSize: '1.3rem',
              lineHeight: '1.4',
              margin: 0,
              color: 'var(--text-main)',
              wordBreak: 'keep-all'
            }}>
              {question?.includes(']') ? question.split(']').slice(1).join(']').trim() : question}
            </h2>
          </div>

          {/* Right: Video Area */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {/* Video Container to ensure absolute positioning works relative to this */}
            <div style={{ position: 'relative', width: '100%', paddingTop: '75%', borderRadius: '20px', overflow: 'hidden', border: '1px solid var(--glass-border)', background: '#000' }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
              />

              {/* [NEW] Vision HUD Overlay - 얼굴 감지된 경우에만 표시 */}
              {visionData && visionData.status === 'detected' && (
                <>
                  {/* 1. Gaze Status (Top Left) */}
                  <div style={{
                    position: 'absolute', top: '1rem', left: '1rem',
                    padding: '6px 12px', borderRadius: '12px',
                    background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                    color: visionData.gaze === 'center' ? '#4ade80' : '#f87171',
                    border: '1px solid rgba(255,255,255,0.2)',
                    fontSize: '0.9rem', fontWeight: 'bold'
                  }}>
                    {visionData.gaze === 'center' ? '👀 정면 응시' : `👀 시선 이탈 (${visionData.gaze})`}
                  </div>

                  {/* 2. Emotion Score (Top Right) below recording lamp */}
                  <div style={{
                    position: 'absolute', top: '3.5rem', right: '0.8rem',
                    padding: '6px 12px', borderRadius: '12px',
                    background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                    color: visionData.emotion === 'anxious' ? '#f87171' : '#facc15',
                    border: '1px solid rgba(255,255,255,0.2)',
                    fontSize: '0.9rem', fontWeight: 'bold',
                    textAlign: 'right'
                  }}>
                    <div>{visionData.emotion === 'happy' ? '😊 미소' : (visionData.emotion === 'anxious' ? '😟 긴장' : '😐 평온')}</div>
                    <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>미소: {Math.round(visionData.scores.smile * 100)}%</div>
                    <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>긴장: {Math.round(visionData.scores.anxiety * 100)}%</div>
                  </div>

                  {/* 3. Posture/Head (Bottom Center) */}
                  {visionData.head === 'unstable' && (
                    <div style={{
                      position: 'absolute', bottom: '1rem', left: '50%', transform: 'translateX(-50%)',
                      padding: '6px 12px', borderRadius: '12px',
                      background: 'rgba(239, 68, 68, 0.8)', color: 'white',
                      fontSize: '0.9rem', fontWeight: 'bold'
                    }}>
                      🚫 고개 흔들림 감지
                    </div>
                  )}
                </>
              )}

              {/* Recording Status Lamp */}
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
                  {isRecording ? 'LIVE REC' : (isMediaReady ? 'READY' : 'CONNECTING...')}
                </span>
              </div>
              {!isMediaReady && (
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'rgba(0,0,0,0.6)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  gap: '10px'
                }}>
                  <div className="spinner" style={{ width: '30px', height: '30px', borderTopColor: 'var(--primary)' }}></div>
                  <span style={{ fontSize: '0.9rem' }}>장비 연결 중...</span>
                </div>
              )}
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
          overflowY: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <h4 style={{
            color: isRecording ? '#ef4444' : 'var(--text-muted)',
            marginBottom: '0.8rem',
            fontSize: '0.8rem',
            fontWeight: '600',
            textTransform: 'uppercase'
          }}>
            {isRecording ? '🎤 실시간 인식 중...' : '답변 입력'}
          </h4>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            readOnly={isRecording}
            placeholder={isRecording ? '음성 인식 대기 중...' : '마이크를 사용할 수 없는 경우 이곳에 직접 답변을 입력하고 Enter를 눌러주세요.'}
            style={{
              flex: 1,
              width: '100%',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: transcript ? 'var(--text-main)' : 'var(--text-muted)',
              fontSize: '1.1rem',
              lineHeight: '1.5',
              resize: 'none',
              fontFamily: 'inherit',
              padding: 0
            }}
          />
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
            disabled={!isMediaReady}
            onClick={() => {
              console.log('[InterviewPage] 답변 버튼 클릭:', isRecording ? '종료' : '시작');
              toggleRecording();
            }}
            style={{
              flex: 1,
              minWidth: '140px',
              padding: '1rem',
              fontSize: '1rem',
              fontWeight: '700',
              opacity: isMediaReady ? 1 : 0.6
            }}
          >
            {!isMediaReady ? '⏳ 준비 중' : (isRecording ? '⏸ 답변 종료' : '답변 시작')}
          </PremiumButton>
          <PremiumButton
            onClick={nextQuestion}
            disabled={isRecording || isLoading || transcript.trim().length === 0}
            style={{ 
              flex: 1, 
              minWidth: '140px', 
              padding: '1rem', 
              fontSize: '1rem', 
              fontWeight: '700',
              opacity: (isRecording || isLoading || transcript.trim().length === 0) ? 0.6 : 1,
              cursor: (isRecording || isLoading || transcript.trim().length === 0) ? 'not-allowed' : 'pointer'
            }}
          >
            {currentIdx < totalQuestions - 1 ? '다음 질문' : '답변 완료 (다음 단계)'}
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
                {"면접을 종료하면 현재까지의 답변을 바탕으로\nAI 분석 리포트가 생성됩니다.\n정말로 면접을 마무리하시겠습니까?"}
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