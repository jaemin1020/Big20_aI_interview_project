import React, { useState, useEffect, useRef } from 'react';
import GlassCard from '../../components/layout/GlassCard';
import PremiumButton from '../../components/ui/PremiumButton';

const EnvTestPage = ({ onNext }) => {
  const [step, setStep] = useState('audio'); // audio, video
  const [audioLevel, setAudioLevel] = useState(0);
  const [isRecognitionOk, setIsRecognitionOk] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [videoStream, setVideoStream] = useState(null);
  const [isFaceDetected, setIsFaceDetected] = useState(false);

  // 수동 제어를 위한 상태
  const [isRecording, setIsRecording] = useState(false);
  const [logs, setLogs] = useState([]); // 대화 로그

  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');

  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  const audioContextRef = useRef(null);
  const animationFrameRef = useRef(null);
  const sourceRef = useRef(null);
  const audioChunksRef = useRef([]); // 청크 저장용 Ref (Closure 문제 방지)

  // 마이크 목록 불러오기
  useEffect(() => {
    const getDevices = async () => {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true }); // 권한 요청
        const devices = await navigator.mediaDevices.enumerateDevices();
        const mics = devices.filter(d => d.kind === 'audioinput');
        setAudioDevices(mics);
        if (mics.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(mics[0].deviceId);
        }
      } catch (err) {
        console.error("Device verification failed:", err);
        setAudioDevices([{ deviceId: 'default', label: 'Default Microphone' }]);
        setSelectedDeviceId('default');
      }
    };
    getDevices();
  }, []);

  // 오디오 스트림 및 레벨 미터 설정
  useEffect(() => {
    const setupAudio = async () => {
      if (step !== 'audio') return;

      try {
        const constraints = selectedDeviceId && selectedDeviceId !== 'default'
          ? { audio: { deviceId: { exact: selectedDeviceId } } }
          : { audio: true };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);

        // Audio Context 설정
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;

        const analyser = audioContext.createAnalyser();
        const microphone = audioContext.createMediaStreamSource(stream);
        sourceRef.current = microphone;

        analyser.smoothingTimeConstant = 0.8;
        analyser.fftSize = 1024;
        microphone.connect(analyser);

        const updateLevel = () => {
          const array = new Uint8Array(analyser.frequencyBinCount);
          analyser.getByteFrequencyData(array);
          let values = 0;
          for (let i = 0; i < array.length; i++) values += array[i];
          const average = values / array.length;
          setAudioLevel(Math.min(100, Math.max(0, average * 2)));
          animationFrameRef.current = requestAnimationFrame(updateLevel);
        };
        updateLevel();

        // MediaRecorder 준비
        let mediaRecorder;
        try {
          mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        } catch (e) {
          console.warn("audio/webm not supported, trying default");
          mediaRecorder = new MediaRecorder(stream);
        }

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          audioChunksRef.current = []; // Clear

          if (audioBlob.size < 100) {
            console.log("Audio blob too small, skipping STT");
            setIsRecording(false);
            return;
          }

          console.log(`Sending STT request... Size: ${audioBlob.size} bytes`);
          // STT 요청
          try {
            const formData = new FormData();
            formData.append('file', audioBlob, 'audio.webm');

            const response = await fetch('http://localhost:8000/stt/recognize', {
              method: 'POST',
              body: formData
            });

            if (response.ok) {
              const result = await response.json();
              const text = (result.text || '').trim();
              if (text && text !== '-') { // 하이픈 필터링
                const timestamp = new Date().toLocaleTimeString();
                setLogs(prev => [...prev, { time: timestamp, text: text }]);
                setTranscript(prev => `${prev} ${text}`);
                setIsRecognitionOk(true);
              } else {
                console.log("No valid text recognized");
              }
            } else {
              console.error('STT API Error:', response.status);
            }
          } catch (e) {
            console.error("STT Request Error:", e);
          }

          setIsRecording(false); // 상태 확실하게 끔
        };

        mediaRecorderRef.current = mediaRecorder;

      } catch (e) {
        console.error("Mic access error:", e);
      }
    };

    setupAudio();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (sourceRef.current) sourceRef.current.disconnect();
      if (audioContextRef.current) audioContextRef.current.close();
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    };
  }, [step, selectedDeviceId]);

  // 화면 스크롤 하단 고정용
  const logsEndRef = useRef(null);
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // 단순화된 녹음 제어 로직 (통녹음)
  const handleStartRecording = async () => {
    // AudioContext Resume
    if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume();
    }

    if (isRecording) return;
    if (!mediaRecorderRef.current) return;

    setIsRecording(true);
    audioChunksRef.current = []; // 시작 전 초기화
    setLogs([]); // 새 테스트 시 로그 초기화 (원하면 유지 가능)
    setTranscript("");

    try {
      mediaRecorderRef.current.start();
      console.log("Recording started...");
    } catch (e) {
      console.error("Recording start error:", e);
      setIsRecording(false);
    }
  };

  const handleStopRecording = () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return;

    console.log("Stopping recording...");
    mediaRecorderRef.current.stop(); // 이 때 onstop 이벤트가 발생하여 STT 요청함
    // setIsRecording(false)는 onstop에서 처리됨
  };

  const handleRetry = () => {
    setTranscript('');
    setLogs([]);
    setIsRecognitionOk(false);
    handleStopRecording();
  };

  const handleNext = () => {
    handleStopRecording();
    setStep('video');
  };

  // --------------------------------------------------------------------------
  // RENDER Helpers
  // --------------------------------------------------------------------------
  const renderVideoStep = () => {
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
            {/* Face Detection UI */}
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '200px',
              height: '250px',
              border: isFaceDetected ? '3px solid #10b981' : '2px solid var(--secondary)',
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
            <PremiumButton onClick={onNext} style={{ flex: 1 }}>다음 단계 진행</PremiumButton>
            <PremiumButton variant="secondary" onClick={() => setStep('audio')}>오디오 테스트 다시 하기</PremiumButton>
          </div>
        </GlassCard>
      </div>
    );
  };

  // Video Step Effect (Always run, but condition check inside)
  useEffect(() => {
    let currentStream = null;

    if (step === 'video') {
      const startVideo = async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
          currentStream = stream;
          setVideoStream(stream);
          if (videoRef.current) videoRef.current.srcObject = stream;
          setTimeout(() => setIsFaceDetected(true), 2000);
        } catch (err) {
          console.error("Camera access failed:", err);
        }
      };
      startVideo();
    }

    return () => {
      // Cleanup happens when effect re-runs or unmounts
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
      }
      if (videoStream) { // Also clean up state stream if exists
        videoStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [step]); // Dependency on step

  if (step === 'video') {
    return renderVideoStep();
  }

  // --------------------------------------------------------------------------
  // RENDER (Audio)
  // --------------------------------------------------------------------------
  return (
    <div className="audio-test animate-fade-in" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', width: '100%', padding: '2rem 0' }}>
      <GlassCard style={{ maxWidth: '600px', width: '100%', textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-wrapper" style={{ width: '160px' }}>
            <img src="/logo.png" alt="BIGVIEW" className="theme-logo" />
          </div>
        </div>
        <h1 className="text-gradient">음성테스트를 시작합니다.</h1>
        <p style={{ marginBottom: '2rem' }}>마이크가 정상적으로 작동하는지 확인합니다.</p>

        <div style={{ margin: '2rem 0' }}>
          <img
            src="/mic_icon.png"
            alt="Microphone"
            style={{
              width: '64px',
              height: '64px',
              objectFit: 'contain',
              filter: isRecording ? 'drop-shadow(0 0 15px var(--primary))' : 'grayscale(100%)',
              marginBottom: '1.5rem',
              transition: 'filter 0.3s'
            }}
          />
          <p style={{ fontSize: '1.1rem', fontWeight: '500', color: 'var(--text-main)', marginBottom: '1rem' }}>
            아래 텍스트를 읽어보세요:
          </p>
          <p style={{ fontSize: '1.2rem', fontWeight: '600', color: 'var(--primary)', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '12px' }}>
            "AI 모의면접 진행할 준비가 되었습니다."
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          {/* 마이크 선택 UI */}
          <div style={{ marginBottom: '1rem', textAlign: 'left' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>마이크 선택</label>
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '8px',
                border: '1px solid var(--glass-border)',
                background: 'rgba(255, 255, 255, 0.05)',
                color: 'var(--text-main)',
                outline: 'none'
              }}
            >
              {audioDevices.map(device => (
                <option key={device.deviceId} value={device.deviceId} style={{ background: '#333' }}>
                  {device.label || `Microphone ${device.deviceId.slice(0, 5)}...`}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            <span>마이크 입력 레벨</span>
            <span>{Math.round(audioLevel)}%</span>
          </div>
          <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${audioLevel}%`, height: '100%', background: isRecording ? 'var(--primary)' : '#555', transition: 'width 0.1s' }}></div>
          </div>
        </div>

        {/* 수동 제어 버튼 (통녹음 방식) */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
          {!isRecording ? (
            <PremiumButton onClick={handleStartRecording} style={{ flex: 1, background: 'var(--primary)' }}>
              ▶ 녹음 시작
            </PremiumButton>
          ) : (
            <PremiumButton onClick={handleStopRecording} style={{ flex: 1, background: '#ef4444' }}>
              ⏹ 녹음 종료 (결과 확인)
            </PremiumButton>
          )}
        </div>

        {/* 로그 박스 */}
        <div style={{
          height: '150px',
          overflowY: 'auto',
          background: 'var(--bg-darker)',
          borderRadius: '12px',
          padding: '1rem',
          marginBottom: '2rem',
          border: '1px solid var(--glass-border)',
          textAlign: 'left',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', position: 'sticky', top: 0, background: 'var(--bg-darker)', paddingBottom: '5px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            인식 결과 {isRecording && <span style={{ color: '#ef4444', animation: 'blink 1s infinite' }}>● Recording...</span>}
          </span>
          {logs.length === 0 && !isRecording && <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '1rem', textAlign: 'center' }}>녹음 버튼을 누르고 문장을 다 읽은 뒤 종료를 누르세요.</span>}
          {logs.map((log, idx) => (
            <div key={idx} style={{ fontSize: '0.95rem', color: 'var(--text-main)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '4px' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginRight: '8px' }}>[{log.time}]</span>
              {log.text}
            </div>
          ))}
          <div ref={logsEndRef}></div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <PremiumButton onClick={handleRetry} variant="secondary" style={{ flex: 1 }}>
            초기화
          </PremiumButton>
          <PremiumButton
            onClick={handleNext}
            style={{ flex: 1 }}
            disabled={!isRecognitionOk}
          >
            다음 진행
          </PremiumButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default EnvTestPage;
