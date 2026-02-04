import { useState, useRef, useEffect } from 'react';
import { 
  createInterview, 
  getInterviewQuestions, 
  createTranscript,
  completeInterview,
  getEvaluationReport,
  uploadResume,
  getAllInterviews,
  login as apiLogin, 
  register as apiRegister, 
  logout as apiLogout, 
  getCurrentUser 
} from './api/interview';
import { createClient } from "@deepgram/sdk";

// Layout & UI
import Header from './components/layout/Header';
import MainPage from './pages/main/MainPage';
import AuthPage from './pages/auth/AuthPage';
import LandingPage from './pages/landing/LandingPage';
import GuidePage from './pages/landing/GuidePage';
import ResumePage from './pages/landing/ResumePage';
import EnvTestPage from './pages/setup/EnvTestPage';
import FinalGuidePage from './pages/landing/FinalGuidePage';
import InterviewPage from './pages/interview/InterviewPage';
import ResultPage from './pages/result/ResultPage';

function App() {
  const [step, setStep] = useState('main'); 
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');
  
  const [isDarkMode, setIsDarkMode] = useState(false); // 기본: 라이트모드

  useEffect(() => {
    console.log("Theme changed to:", isDarkMode ? "DARK" : "LIGHT");
    if (isDarkMode) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  }, [isDarkMode]);
  
  const [account, setAccount] = useState({ 
    email: '', 
    password: '', 
    passwordConfirm: '',
    fullName: '', 
    birthDate: '',
    profileImage: null,
    termsAgreed: false
  });
  const [interview, setInterview] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [report, setReport] = useState(null);
  
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [userName, setUserName] = useState('');
  const [position, setPosition] = useState('');
  const [resumeFile, setResumeFile] = useState(null);

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);
  
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const deepgramConnectionRef = useRef(null);
  const isRecordingRef = useRef(false);
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getCurrentUser()
        .then(u => {
          setUser(u);
          setStep('landing');
        })
        .catch(() => {
          localStorage.removeItem('token');
          setStep('main');
        });
    }
  }, []);

  const handleAuth = async () => {
    setAuthError('');
    
    // 클라이언트 사이드 유효성 검사
    if (authMode === 'register') {
        const usernameRegex = /^[a-z0-9_]{4,12}$/;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!usernameRegex.test(account.username)) {
            setAuthError("아이디는 4~12자의 영문 소문자, 숫자, 밑줄(_)만 가능합니다.");
            return;
        }
        if (!emailRegex.test(account.email)) {
            setAuthError("유효한 이메일 주소를 입력해주세요.");
            return;
        }
    }

    try {
      if (authMode === 'login') {
        // 로그인 시에는 email을 username으로 사용
        await apiLogin(account.email, account.password);
        const u = await getCurrentUser();
        setUser(u);
        setStep('landing');
      } else {
        // 회원가입 검증
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(account.email)) {
          setAuthError('올바른 이메일 형식이 아닙니다.');
          return;
        }

        if (account.password !== account.passwordConfirm) {
          setAuthError('비밀번호가 일치하지 않습니다.');
          return;
        }
        if (!account.termsAgreed) {
          setAuthError('이용약관에 동의해야 합니다.');
          return;
        }

        // 실제 API 호출 (백엔드 맞춰서 email을 username으로 전달)
        await apiRegister(account.email, account.password, account.fullName);
        alert('회원가입 성공! 로그인해주세요.');
        setAuthMode('login');
      }
    } catch (err) {
      // FastAPI validation error (422) 처리
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          // Validation error 배열
          setAuthError(detail.map(e => e.msg).join(', '));
        } else if (typeof detail === 'string') {
          setAuthError(detail);
        } else {
          setAuthError('인증 실패');
        }
      } else {
        setAuthError(err.message || '인증 실패');
      }
    }
  };

  const handleLogout = () => {
    apiLogout();
    setUser(null);
    setStep('auth');
  };

  const startInterviewFlow = async (uName, uPos) => {
    if (!uName.trim() || !uPos.trim()) {
      alert("이름과 지원 직무를 입력해주세요.");
      return;
    }
    setUserName(uName);
    setPosition(uPos);
    setStep('resume');
  };

  const initInterviewSession = async () => {
    try {
      // 1. Create Interview
      const newInterview = await createInterview(userName, position);
      setInterview(newInterview);

      // 2. Upload Resume if available
      if (resumeFile) {
        await uploadResume(newInterview.id, resumeFile);
      }

      // 3. Get Questions
      const qs = await getInterviewQuestions(newInterview.id);
      
      // Retry logic if questions are not ready (optional, but good for UX)
      if (!qs || qs.length === 0) {
         console.log("Questions not ready, retrying in 3s...");
         setTimeout(async () => {
             const retryQs = await getInterviewQuestions(newInterview.id);
             setQuestions(retryQs);
             setStep('interview');
         }, 3000);
         return;
      }

      setQuestions(qs);
      setStep('interview');
    } catch (err) {
      console.error("Session init error:", err);
      alert("면접 세션 생성에 실패했습니다.");
    }
  };

  const setupWebSocket = (sessionId) => {
    const ws = new WebSocket(`ws://localhost:8080/ws/${sessionId}`);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'stt_result' && data.text) {
          setTranscript(prev => prev + ' ' + data.text);
        }
      } catch (err) { console.error('[WS] Parse error:', err); }
    };
  };

  const setupDeepgram = (stream) => {
    const apiKey = import.meta.env.VITE_DEEPGRAM_API_KEY;
    if (!apiKey) {
      console.warn("Deepgram API Key not found");
      return;
    }

    const deepgram = createClient(apiKey);
    const connection = deepgram.listen.live({
      model: "nova-2",
      language: "ko",
      smart_format: true,
      encoding: "linear16", 
      sample_rate: 16000,
    });

    connection.on("Open", () => {
      console.log("Deepgram WebSocket Connected");
      
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
        const transcriptText = channel.alternatives[0].transcript;
        const isFinal = result.is_final;
        
        if (transcriptText) {
          if (isFinal) {
             setTranscript(prev => prev + ' ' + transcriptText);
             setSubtitle(''); 
          } else {
             setSubtitle(transcriptText);
          }
        }
      }
    });

    connection.on("Error", (err) => {
      console.error("Deepgram Error:", err);
    });

    deepgramConnectionRef.current = connection;
  };

  const setupWebRTC = async (interviewId) => {
    console.log('[WebRTC] Starting setup for interview:', interviewId);
    const pc = new RTCPeerConnection();
    pcRef.current = pc;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (videoRef.current) videoRef.current.srcObject = stream;
      stream.getTracks().forEach(track => pc.addTrack(track, stream));
    } catch (err) { console.warn('[WebRTC] Access failed:', err); }

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    const response = await fetch('http://localhost:8080/offer', {
      method: 'POST',
      body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type, session_id: sessionId }),
      headers: { 'Content-Type': 'application/json' }
    });
    const answer = await response.json();
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
    console.log('[WebRTC] Connection established successfully');
  };

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
    } else {
      setTranscript('');
      setIsRecording(true);
    }
  };

  const drawTracking = (trackingData) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video || video.videoWidth === 0) return;

    const ctx = canvas.getContext('2d');
    
    // Canvas 크기를 비디오 표시 크기에 맞춤 (한 번만 설정하거나 리사이즈 이벤트 처리 필요하지만 여기선 매번 체크)
    if (canvas.width !== video.clientWidth || canvas.height !== video.clientHeight) {
        canvas.width = video.clientWidth;
        canvas.height = video.clientHeight;
    }
    
    // Clear
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Scale Factors
    const scaleX = video.clientWidth / video.videoWidth;
    const scaleY = video.clientHeight / video.videoHeight;

    trackingData.forEach(item => {
        // Face (Green)
        if (item.face) {
            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 2;
            ctx.strokeRect(
                item.face.x * scaleX, 
                item.face.y * scaleY, 
                item.face.w * scaleX, 
                item.face.h * scaleY
            );
        }

        // Eyes (Red)
        if (item.eyes) {
            item.eyes.forEach(eye => {
                ctx.strokeStyle = '#ff0000';
                ctx.lineWidth = 2;
                ctx.strokeRect(
                    eye.x * scaleX, 
                    eye.y * scaleY, 
                    eye.w * scaleX, 
                    eye.h * scaleY
                );
            });
        }
    });
  };

  const nextQuestion = async () => {
    const answerText = transcript.trim() || "답변 내용 없음";
    try {
      await submitAnswer(questions[currentIdx].id, answerText);
      if (currentIdx < questions.length - 1) {
        setCurrentIdx(currentIdx + 1);
        setTranscript('');
        setIsRecording(false);
      } else {
        setStep('loading');
        if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
        if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
        setTimeout(async () => {
          const res = await getResults(session.id);
          setResults(res);
          setStep('result');
        }, 5000);
      }
    } catch (err) {
      alert('답변 제출에 실패했습니다.');
    }
  };

  useEffect(() => {
    if (step === 'interview' && session && videoRef.current && !pcRef.current) {
      setupWebRTC(session.id);
      setupWebSocket(session.id);
    }
  }, [step, interview]);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pcRef.current) pcRef.current.close();
    };
  }, []);

  return (
    <div className="container">
      {/* Header - Visible in Most Steps */}
      {step !== 'main' && step !== 'auth' && (
        <Header 
          onLogout={handleLogout} 
          showLogout={!!user} 
          onLogoClick={() => setStep('main')} 
        />
      )}

      {/* Theme Toggle Button */}
      <div style={{ position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 1000 }}>
        <button 
          onClick={() => setIsDarkMode(!isDarkMode)}
          style={{ 
            width: '50px', 
            height: '50px', 
            borderRadius: '50%', 
            background: 'var(--glass-bg)',
            backdropFilter: 'blur(10px)',
            border: '1px solid var(--glass-border)',
            boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
            cursor: 'pointer',
            fontSize: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.3s ease'
          }}
        >
          {isDarkMode ? '☀️' : '🌙'}
        </button>
      </div>

      <div style={{ flex: 1, width: '100%', display: 'flex', flexDirection: 'column' }}>
        {step === 'main' && (
          <MainPage 
            onStartInterview={() => setStep('landing')}
            onLogin={() => { setAuthMode('login'); setStep('auth'); }}
            onRegister={() => { setAuthMode('register'); setStep('auth'); }}
          />
        )}

      {step === 'auth' && (
        <AuthPage 
          authMode={authMode} setAuthMode={setAuthMode}
          account={account} setAccount={setAccount}
          handleAuth={handleAuth} authError={authError}
        />
      )}

      {step === 'landing' && (
        <LandingPage 
          userName={userName} setUserName={setUserName}
          position={position} setPosition={setPosition}
          startInterview={startInterviewFlow} handleLogout={handleLogout}
        />
      )}

      {step === 'guide' && <GuidePage onNext={() => setStep('resume')} />}
      
      {step === 'resume' && <ResumePage onNext={() => setStep('env_test')} onFileSelect={setResumeFile} />}
      
      {step === 'env_test' && <EnvTestPage onNext={() => setStep('final_guide')} />}
      
      {step === 'final_guide' && <FinalGuidePage onNext={initInterviewSession} onPrev={() => setStep('env_test')} />}

      {step === 'interview' && (
        <InterviewPage 
          currentIdx={currentIdx}
          totalQuestions={questions.length}
          question={questions[currentIdx]?.question_text}
          isRecording={isRecording}
          transcript={transcript}
          toggleRecording={toggleRecording}
          nextQuestion={nextQuestion}
          videoRef={videoRef}
        />
      )}

      {step === 'loading' && (
        <div className="card animate-fade-in" style={{ textAlign: 'center' }}>
          <h2 className="text-gradient">AI 분석 리포트 생성 중...</h2>
          <div className="spinner" style={{ width: '60px', height: '60px', borderTopColor: 'var(--primary)' }}></div>
          <p style={{ color: 'var(--text-muted)' }}>답변 내용을 바탕으로 정밀한 결과를 도출하고 있습니다. 잠시만 기다려주세요.</p>
        </div>
      )}

      {step === 'result' && (
        <ResultPage 
          results={report || []} 
          onReset={() => {
            setStep('landing');
            setCurrentIdx(0);
            setReport(null);
          }} 
        />
      )}
      </div>
    </div>
  );
}

export default App;