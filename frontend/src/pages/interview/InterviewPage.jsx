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
  toggleRecording,
  nextQuestion,
  onFinish,
  videoRef,
  isLoading,
  visionData // [NEW] Receive vision data
}) => {
  const [timeLeft, setTimeLeft] = React.useState(60);
  const [showTooltip, setShowTooltip] = React.useState(false);
  // 이전 질문 인덱스를 추적하여 질문 변경 시 상태를 즉시 리셋 (Stale State 방지)
  const [prevIdx, setPrevIdx] = React.useState(currentIdx);

  const audioRef = React.useRef(null);
  const isTimeOverRef = React.useRef(false); // 타이머 종료 처리 중복 방지용 Ref

  // 질문이 변경되면 렌더링 도중 즉시 상태 리셋
  if (currentIdx !== prevIdx) {
    setPrevIdx(currentIdx);
    setTimeLeft(60);
    isTimeOverRef.current = false;
  }

  React.useEffect(() => {
    setTimeLeft(60); // 질문이 바뀔 때마다 60초로 리셋

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

  React.useEffect(() => {
    // 타이머 기능 활성화
    if (timeLeft <= 0) {
      // 이미 타이머 종료 처리를 했다면 중복 호출 방지
      if (isTimeOverRef.current) return;

      if (!isRecording) {
        console.log("Time over, moving to next question.");
        isTimeOverRef.current = true; // 처리 완료 플래그 설정
        // [수정: 2026-02-12] 타임아웃 시에도 비전 데이터 전송 & 로그 출력
        // 이전 코드: nextQuestion(calculateVisionStats())
        const stats = getVisionStatsAndLog();
        nextQuestion(stats);
      }
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


  // [NEW] 비전 데이터 누적을 위한 Ref
  const visionLogsRef = React.useRef([]);

  // [NEW] 녹음 중일 때 비전 데이터 수집
  // [NEW] 녹음 중일 때 비전 데이터 수집
  // [수정: 2026-02-12] isRecording 상태와 무관하게 현재 질문에 대한 데이터를 계속 수집 (데이터 부족 방지)
  React.useEffect(() => {
    if (visionData) {
      visionLogsRef.current.push({
        timestamp: Date.now(),
        ...visionData
      });
    }
  }, [visionData]);

  // [NEW] MediaPipe 데이터 수신 확인 로그 (사용자 검증용 - 항상 출력)
  React.useEffect(() => {
    if (visionData && visionData.status === 'detected') {
      // [수정: 2026-02-12] 사용자 요청으로 로그 항상 출력 (디버깅용)
      // 기존 5% 확률 제한 제거 -> 매 프레임마다 로그가 찍히면 너무 많으므로 1초에 한번 정도만 찍히게는 못하지만,
      // 일단 사용자가 '작동 여부'를 궁금해하므로 매번 찍거나, UI에 표시하는게 나음.
      // 여기서는 콘솔에 확실히 찍히도록 함.
      console.log(`[MediaPipe] 👁️ Vision Data: Emotion=${visionData.emotion} | Gaze=${visionData.gaze} | Score=${JSON.stringify(visionData.scores)}`);
    }
  }, [visionData]);

  // [NEW] 질문 변경 시 비전 로그 초기화
  React.useEffect(() => {
    visionLogsRef.current = [];
  }, [currentIdx]);

  // [NEW] 비전 데이터 통계 계산 함수
  const calculateVisionStats = () => {
    const logs = visionLogsRef.current;
    if (logs.length === 0) return null;

    const totalFrames = logs.length;
    let gazeCenterCount = 0;
    let postureStableCount = 0; // [NEW] 자세 안정 카운트 추가
    let emotionCounts = { happy: 0, neutral: 0, anxious: 0, angry: 0, sad: 0, surprised: 0 };
    let totalSmileScore = 0;
    let totalAnxietyScore = 0;

    logs.forEach(log => {
      // 1. 시선 (Media-Server에서 'center'로 준 것)
      if (log.gaze === 'center') gazeCenterCount++;

      // 2. 자세 (Media-Server에서 'stable'로 준 것)
      if (log.posture === 'stable') postureStableCount++;

      // 3. 감정
      if (log.emotion) emotionCounts[log.emotion] = (emotionCounts[log.emotion] || 0) + 1;

      // 4. 점수
      if (log.scores) {
        totalSmileScore += (log.scores.smile || 0);
        totalAnxietyScore += (log.scores.anxiety || 0);
      }
    });

    return {
      duration_frames: totalFrames,
      gaze_center_pct: Math.round((gazeCenterCount / totalFrames) * 100),
      posture_stable_pct: Math.round((postureStableCount / totalFrames) * 100), // [NEW] 추가
      emotion_distribution: emotionCounts,
      avg_smile_score: totalSmileScore / totalFrames,
      avg_anxiety_score: totalAnxietyScore / totalFrames,
      timestamp: Date.now()
    };
  };

  // [NEW] 비전 데이터 집계 및 로그 출력 (사용자 검증용)
  const getVisionStatsAndLog = () => {
    const stats = calculateVisionStats();
    if (stats) {
      console.log(`\n============== [Q${currentIdx + 1} Vision Analysis Result] ==============`);
      console.log(`✅ 총 분석 프레임: ${stats.duration_frames}`);
      console.log(`👀 시선 집중도: ${stats.gaze_center_pct}% (정면 응시 비율)`);
      console.log(`😊 평균 미소 점수: ${(stats.avg_smile_score * 100).toFixed(1)}점`);
      console.log(`😟 평균 긴장 점수: ${(stats.avg_anxiety_score * 100).toFixed(1)}점`);
      console.log(`📊 감정 분포: Happy=${stats.emotion_distribution.happy}, Anxious=${stats.emotion_distribution.anxious}, Neutral=${stats.emotion_distribution.neutral}`);
      console.log(`=============================================================\n`);
    } else {
      console.warn(`[Q${currentIdx + 1}] 비전 데이터가 충분하지 않습니다. (분석 실패 가능성)`);
    }
    return stats;
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
            {/* Video Container to ensure absolute positioning works relative to this */}
            <div style={{ position: 'relative', width: '100%', paddingTop: '75%', borderRadius: '20px', overflow: 'hidden', border: '1px solid var(--glass-border)', background: '#000' }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }}
              />

              {/* [NEW] Vision HUD Overlay */}
              {visionData && (
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
            onClick={() => {
              // [NEW] 비전 통계 포함하여 전송
              const stats = calculateVisionStats();
              nextQuestion(stats);
            }}
            disabled={isLoading}
            style={{
              flex: 1,
              minWidth: '140px',
              padding: '1rem',
              fontSize: '1rem',
              fontWeight: '700',
              opacity: isLoading ? 0.6 : 1,
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
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