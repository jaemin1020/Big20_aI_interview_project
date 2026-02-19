import React, { useState, useEffect, useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { recognizeAudio } from '../../api/interview';

const EnvTestPage = ({ onNext, envTestStep, setEnvTestStep }) => {
  const step = envTestStep;
  const setStep = setEnvTestStep;

  // Audio Test States
  const [audioLevel, setAudioLevel] = useState(0);
  const [isRecognitionOk, setIsRecognitionOk] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [audioStream, setAudioStream] = useState(null);

  // Video Test States
  const [videoStream, setVideoStream] = useState(null);
  const [isFaceDetected, setIsFaceDetected] = useState(false);

  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  // 1. Audio Stream & Visualization Setup
  useEffect(() => {
    let audioContext;
    let analyser;
    let microphone;
    let javascriptNode;

    const initAudio = async () => {
      if (step !== 'audio') return;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setAudioStream(stream); // Save for recording

        // Visualization Setup
        audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // 브라우저 정책으로 Suspended 상태일 경우 Resume
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }

        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);

        analyser.smoothingTimeConstant = 0.8;
        analyser.fftSize = 1024;

        microphone.connect(analyser); // Source -> Analyser

        // ScriptProcessor 초기화 (audioLevel 갱신용)
        javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);
        analyser.connect(javascriptNode); // Analyser -> Node
        javascriptNode.connect(audioContext.destination); // Node -> Destination (필수)

        javascriptNode.onaudioprocess = () => {
          const array = new Uint8Array(analyser.frequencyBinCount);
          analyser.getByteFrequencyData(array);
          let values = 0;
          for (let i = 0; i < array.length; i++) values += array[i];

          const average = values / array.length;
          setAudioLevel(Math.min(100, Math.max(0, average * 2)));
        };

      } catch (err) {
        console.error("❌ Microphone access failed:", err);
        alert("마이크 접근이 차단되었거나 찾을 수 없습니다. 설정에서 권한을 확인해주세요.");
      }
    };

    if (step === 'audio') {
      initAudio();
    }

    return () => {
      // Cleanup
      if (javascriptNode) javascriptNode.disconnect();
      if (microphone) microphone.disconnect();
      if (analyser) analyser.disconnect();
      if (audioContext) audioContext.close();

      // Stop stream tracks only when leaving the step completely or unmounting
      // but here we might urge to stop it to release mic
      if (step !== 'audio' && audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [step]); // Dependency on step

  // Cleanup stream on component unmount
  useEffect(() => {
    return () => {
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // 2. Recording & STT Logic
  const handleStartTest = () => {
    if (!audioStream) {
      console.error("No audio stream available");
      return;
    }

    setTranscript('');
    setIsRecognitionOk(false);
    setIsRecording(true);

    try {
      const mediaRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;

      const chunks = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        const blob = new Blob(chunks, { type: 'audio/webm' });
        try {
          console.log("Sending audio for recognition...");
          const result = await recognizeAudio(blob);
          console.log("Recognition Result:", result);

          if (result.text && result.text.trim()) {
            setTranscript(result.text);
            setIsRecognitionOk(true);
          } else {
            setTranscript("음성이 인식되지 않았습니다. 다시 시도해주세요.");
          }
        } catch (err) {
          console.error("STT Error:", err);
          setTranscript("인식 오류가 발생했습니다. (서버 연결 확인 필요)");
        } finally {
          setIsProcessing(false);
          setIsRecording(false); // Ensure reset
        }
      };

      mediaRecorder.start();

      // Auto-stop after 4 seconds
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
          setIsRecording(false);
        }
      }, 4000);
    } catch (err) {
      console.error("MediaRecorder Start Error:", err);
      alert("녹음을 시작할 수 없습니다. (MediaRecorder Error)");
      setIsRecording(false);
    }
  };

  // Video Step Logic
  const startVideo = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setVideoStream(stream);
      if (videoRef.current) videoRef.current.srcObject = stream;

      // Simulate Face Detection
      setTimeout(() => {
        setIsFaceDetected(true);
      }, 2000);
    } catch (err) {
      console.error("Camera access failed:", err);
    }
  };

  useEffect(() => {
    if (step === 'video') {
      startVideo();
    }
    return () => {
      if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [step]);

  const handleRetry = () => {
    setTranscript('');
    setIsRecognitionOk(false);
    setAudioLevel(0);
  };

  const handleVideoPass = () => {
    if (isFaceDetected) sessionStorage.setItem('env_video_ok', 'true');
    else sessionStorage.setItem('env_video_ok', 'false');
    onNext();
  };

  const handleAudioPass = () => {
    if (isRecognitionOk) sessionStorage.setItem('env_audio_ok', 'true');
    else sessionStorage.setItem('env_audio_ok', 'false');

    // Stop audio stream before moving to video
    if (audioStream) audioStream.getTracks().forEach(track => track.stop());
    setStep('video');
  };

  if (step === 'audio') {
    return (
      <div className="audio-test animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%', padding: '2rem 0' }}>
        <GlassCard style={{ maxWidth: '600px', width: '100%', textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-wrapper" style={{ width: '160px' }}>
              <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
            </div>
          </div>
          <h1 className="text-gradient">음성 인식 테스트</h1>
          <p style={{ marginBottom: '2rem' }}>
            마이크가 정상 작동하는지 확인합니다.<br />
            <b>[음성 인식 시작]</b> 버튼을 누르고 <b>"안녕하세요"</b>라고 말씀해보세요.
          </p>

          <div style={{ margin: '2rem 0' }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: isRecording
                ? 'rgba(239, 68, 68, 0.2)' // Red pulse when recording
                : (isRecognitionOk
                  ? 'rgba(16, 185, 129, 0.2)'
                  : 'rgba(255,255,255,0.05)'),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.5rem auto',
              boxShadow: isRecording ? '0 0 15px rgba(239, 68, 68, 0.5)' : (isRecognitionOk ? '0 0 15px rgba(16, 185, 129, 0.5)' : 'none'),
              border: isRecording ? '2px solid #ef4444' : (isRecognitionOk ? '2px solid #10b981' : '1px solid rgba(255, 255, 255, 0.2)'),
              transition: 'all 0.3s ease'

            }}>
              {isProcessing ? (
                <div className="spinner" style={{ width: '30px', height: '30px', borderTopColor: 'var(--primary)' }}></div>
              ) : (
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke={isRecording ? "#ef4444" : (isRecognitionOk ? "#10b981" : "var(--primary)")} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  <line x1="12" y1="19" x2="12" y2="23"></line>
                  <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
              )}
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <PremiumButton
                onClick={handleStartTest}
                disabled={isRecording || isProcessing}
                style={{ minWidth: '180px' }}
              >
                {isRecording ? "녹음 중... (4초)" : (isProcessing ? "분석 중..." : (transcript ? "다시 테스트하기" : "음성 인식 시작"))}
              </PremiumButton>
            </div>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              <span>마이크 입력 레벨</span>
              <span>{Math.round(audioLevel)}%</span>
            </div>
            <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${audioLevel}%`, height: '100%', background: isRecognitionOk ? '#10b981' : 'var(--primary)', transition: 'width 0.1s, background 0.3s' }}></div>
            </div>
          </div>

          <div style={{
            minHeight: '60px',
            background: 'var(--bg-darker)',
            borderRadius: '12px',
            padding: '1rem',
            marginBottom: '2rem',
            border: isRecognitionOk ? '1px solid #10b981' : '1px solid var(--glass-border)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>인식된 결과:</span>
            <span style={{ color: isRecognitionOk ? 'var(--text-main)' : 'var(--text-muted)', fontWeight: isRecognitionOk ? 'bold' : 'normal', fontSize: '1.1rem' }}>
              {transcript || "버튼을 누르고 말씀을 하시면 텍스트로 변환됩니다."}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <PremiumButton onClick={handleAudioPass} variant="secondary" style={{ flex: 1, opacity: 0.7 }}>
              테스트 건너뛰기
            </PremiumButton>
            <PremiumButton
              onClick={handleAudioPass}
              style={{ flex: 1 }}
            >
              다음 진행
            </PremiumButton>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="video-test animate-fade-in" style={{ height: 'calc(100vh - var(--header-height))', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%', overflow: 'hidden', padding: '0.5rem', boxSizing: 'border-box' }}>
      <GlassCard style={{ maxWidth: '800px', width: '100%', textAlign: 'center', maxHeight: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
          <div className="logo-wrapper" style={{ width: '120px' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
        </div>
        <h1 className="text-gradient" style={{ fontSize: '1.5rem', margin: '0 0 0.5rem 0' }}>환경 테스트 - 영상</h1>
        <p style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>카메라를 확인하고 얼굴이 프레임 안에 들어오도록 맞춰주세요.</p>

        <div style={{ position: 'relative', marginBottom: '1rem', flex: 1, minHeight: 0, display: 'flex', justifyContent: 'center' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ width: 'auto', height: '100%', maxHeight: '50vh', objectFit: 'contain', borderRadius: '12px', background: '#000' }}
          />
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '200px',
            height: '250px',
            border: isFaceDetected ? '3px solid #10b981' : '2px solid var(--secondary)', // Green if detected
            borderRadius: '50%',
            pointerEvents: 'none',
            boxShadow: '0 0 0 9999px rgba(0,0,0,0.4)',
            transition: 'border 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {isFaceDetected && (
              <div style={{
                background: '#10b981',
                color: 'white',
                padding: '0.5rem 1rem',
                borderRadius: '20px',
                fontWeight: 'bold',
                fontSize: '0.9rem',
                boxShadow: '0 4px 10px rgba(16, 185, 129, 0.4)'
              }}>
                ✓ 인식 완료
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: 'auto' }}>
          <PremiumButton onClick={handleVideoPass} style={{ flex: 1 }}>다음 단계 진행</PremiumButton>
          <PremiumButton variant="secondary" onClick={() => setStep('audio')}>오디오 테스트 다시 하기</PremiumButton>
        </div>
      </GlassCard>
    </div >
  );
};

export default EnvTestPage;