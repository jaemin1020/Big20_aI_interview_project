import React, { useState, useEffect, useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const EnvTestPage = ({ onNext }) => {
  const [step, setStep] = useState('audio'); // audio, video
  const [audioLevel, setAudioLevel] = useState(0);
  const [isRecognitionOk, setIsRecognitionOk] = useState(false);
  const [videoStream, setVideoStream] = useState(null);
  const videoRef = useRef(null);

  // Real Audio Level Visualization
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
          // Scale average to percentage (0-100)
          // Usually average is low, so we might need to scale it up
          const level = Math.min(100, Math.max(0, average * 2)); 
          setAudioLevel(level);
        };
      } catch (err) {
        console.error("Microphone access failed:", err);
        alert("마이크 접근이 차단되었거나 찾을 수 없습니다.");
      }
    };

    if (step === 'audio') {
      startAudioAnalysis();
    }

    return () => {
      if (javascriptNode) javascriptNode.disconnect();
      if (microphone) microphone.disconnect();
      if (analyser) analyser.disconnect();
      if (audioContext) audioContext.close();
      if (stream) stream.getTracks().forEach(track => track.stop());
    };
  }, [step]);

  // Video Stream Start
  const startVideo = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setVideoStream(stream);
      if (videoRef.current) videoRef.current.srcObject = stream;
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

  const handleAudioDone = () => {
    setIsRecognitionOk(true);
    setTimeout(() => setStep('video'), 1000);
  };

  if (step === 'audio') {
    return (
      <div className="audio-test animate-fade-in">
        <GlassCard style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-wrapper" style={{ width: '160px' }}>
              <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
            </div>
          </div>
          <h1 className="text-gradient">환경 테스트 - 오디오</h1>
          <p style={{ marginBottom: '2rem' }}>마이크가 정상적으로 작동하는지 확인합니다. 아래 문장을 읽어주세요.</p>
          
          <div style={{ margin: '2rem 0' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1.5rem' }}>🎙️</div>
            <p style={{ fontSize: '1.4rem', fontWeight: '600', color: 'var(--primary)', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '12px' }}>
              "AI 모의면접 진행할 준비가 되었습니다."
            </p>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              <span>마이크 입력 레벨</span>
              <span>{Math.round(audioLevel)}%</span>
            </div>
            <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${audioLevel}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.1s' }}></div>
            </div>
          </div>

          <PremiumButton onClick={handleAudioDone} style={{ width: '100%' }}>
            {isRecognitionOk ? '✅ 분석 완료' : '문장 읽기 완료'}
          </PremiumButton>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="video-test animate-fade-in">
      <GlassCard style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
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
            border: '2px solid var(--secondary)',
            borderRadius: '50%',
            pointerEvents: 'none',
            boxShadow: '0 0 0 9999px rgba(0,0,0,0.4)'
          }}></div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <PremiumButton onClick={onNext} style={{ flex: 1 }}>다음 단계 진행</PremiumButton>
          <PremiumButton variant="secondary" onClick={() => setStep('audio')}>오디오 테스트 다시 하기</PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default EnvTestPage;
