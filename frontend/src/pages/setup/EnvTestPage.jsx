import React, { useState, useEffect, useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';
import { createClient } from "@deepgram/sdk";

const EnvTestPage = ({ onNext }) => {
  const [step, setStep] = useState('audio'); // audio, video
  const [audioLevel, setAudioLevel] = useState(0);
  const [isRecognitionOk, setIsRecognitionOk] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [videoStream, setVideoStream] = useState(null);
  const [isFaceDetected, setIsFaceDetected] = useState(false);

  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const deepgramConnectionRef = useRef(null);

  // Real Audio Level Visualization & Deepgram STT
  useEffect(() => {
    let audioContext;
    let analyser;
    let microphone;
    let javascriptNode;
    let stream;

    const startAudioAnalysis = async () => {
      if (step !== 'audio') return;

      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // 1. Audio Level Visualization
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

        analyser.smoothingTimeConstant = 0.8;
        analyser.fftSize = 1024;

        microphone.connect(analyser);
        analyser.connect(javascriptNode);
        javascriptNode.connect(audioContext.destination);

        javascriptNode.onaudioprocess = () => {
          const array = new Uint8Array(analyser.frequencyBinCount);
          analyser.getByteFrequencyData(array);
          let values = 0;

          const length = array.length;
          for (let i = 0; i < length; i++) {
            values += array[i];
          }

          const average = values / length;
          const level = Math.min(100, Math.max(0, average * 2));
          setAudioLevel(level);
        };

        // 2. Deepgram STT Setup
        const apiKey = import.meta.env.DEEPGRAM_API_KEY;
        if (apiKey) {
          const deepgram = createClient(apiKey);
          const connection = deepgram.listen.live({
            model: "nova-2",
            language: "ko",
            smart_format: true,
            encoding: "linear16",
            sample_rate: 16000,
            interim_results: true,
          });

          connection.on("Open", () => {
            console.log("Deepgram Connected for Test");

            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorder.addEventListener('dataavailable', (event) => {
              if (event.data.size > 0 && connection.getReadyState() === 1) {
                connection.send(event.data);
              }
            });
            mediaRecorder.start(250);
            mediaRecorderRef.current = mediaRecorder;
          });

          connection.on("Results", (result) => {
            const channel = result.channel;
            if (channel && channel.alternatives && channel.alternatives[0]) {
              const text = channel.alternatives[0].transcript;
              if (text && text.trim().length > 0) {
                setTranscript(prev => {
                  // 간단한 이어붙이기 (실제로는 interim 처리 등 더 복잡할 수 있음)
                  if (result.is_final) return prev + ' ' + text;
                  return prev;
                });
                // 텍스트가 조금이라도 인식되면 성공으로 간주
                if (result.is_final) setIsRecognitionOk(true);
              }
            }
          });

          deepgramConnectionRef.current = connection;
        }

      } catch (err) {
        console.error("Microphone access failed:", err);
        alert("마이크 접근이 차단되었거나 찾을 수 없습니다.");
      }
    };

    if (step === 'audio') {
      startAudioAnalysis();
    }

    return () => {
      // Clean up Audio Context
      if (javascriptNode) javascriptNode.disconnect();
      if (microphone) microphone.disconnect();
      if (analyser) analyser.disconnect();
      if (audioContext) audioContext.close();

      // Clean up Deepgram & MediaRecorder
      if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
      if (deepgramConnectionRef.current) deepgramConnectionRef.current.finish();

      // Stop Tracks
      if (stream) stream.getTracks().forEach(track => track.stop());
    };
  }, [step]);

  // Video Stream Start
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
  };

  const handleVideoPass = () => {
    // Save video test result
    if (isFaceDetected) {
      sessionStorage.setItem('env_video_ok', 'true');
    } else {
      sessionStorage.setItem('env_video_ok', 'false');
    }
    onNext();
  };

  // Save audio test result when moving to video step
  const handleAudioPass = () => {
    if (isRecognitionOk) {
      sessionStorage.setItem('env_audio_ok', 'true');
    } else {
      sessionStorage.setItem('env_audio_ok', 'false');
    }
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
          <h1 className="text-gradient">음성테스트를 시작합니다.</h1>
          <p style={{ marginBottom: '2rem' }}>마이크가 정상적으로 작동하는지 확인합니다. 아래 문장을 읽어주세요.</p>

          <div style={{ margin: '2rem 0' }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.5rem auto',
              boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
              </svg>
            </div>
            <p style={{ fontSize: '1.4rem', fontWeight: '600', color: 'var(--primary)', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '12px' }}>
              "AI 모의면접 진행할 준비가 되었습니다. "
            </p>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              <span>마이크 입력 레벨 {audioLevel > 5 ? '(입력 중...)' : ''}</span>
              <span>{Math.round(audioLevel)}%</span>
            </div>
            <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${audioLevel}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.1s' }}></div>
            </div>
          </div>

          {/* Transcript Box */}
          <div style={{
            minHeight: '80px',
            background: 'var(--bg-darker)',
            borderRadius: '12px',
            padding: '1rem',
            marginBottom: '2rem',
            border: '1px solid var(--glass-border)',
            textAlign: 'left'
          }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem' }}>인식된 텍스트:</span>
            <span style={{ color: transcript ? 'var(--text-main)' : 'var(--text-muted)' }}>
              {transcript || "말씀하시면 이곳에 텍스트가 표시됩니다..."}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <PremiumButton onClick={handleRetry} variant="secondary" style={{ flex: 1 }}>
              테스트 다시 진행
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
    <div className="video-test animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%', padding: '2rem 0' }}>
      <GlassCard style={{ maxWidth: '800px', width: '100%', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-wrapper" style={{ width: '160px' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
        </div>
        <h1 className="text-gradient">환경 테스트 - 영상</h1>
        <p style={{ marginBottom: '2rem' }}>카메라를 확인하고 얼굴이 프레임 안에 들어오도록 맞춰주세요.</p>

        <div style={{ position: 'relative', marginBottom: '2rem' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ width: '100%', borderRadius: '20px', background: '#000' }}
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

        <div style={{ display: 'flex', gap: '1rem' }}>
          <PremiumButton onClick={handleVideoPass} style={{ flex: 1 }}>다음 단계 진행</PremiumButton>
          <PremiumButton variant="secondary" onClick={() => setStep('audio')}>오디오 테스트 다시 하기</PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default EnvTestPage;
