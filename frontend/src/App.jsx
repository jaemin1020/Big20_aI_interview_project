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
          console.log('[STT Received]:', data.text, '| Recording:', isRecordingRef.current);
          
          setTranscript(prev => prev + ' ' + data.text);
        }
      } catch (err) {
        console.error('[WebSocket] Parse error:', err);
      }
    };

    ws.onerror = (error) => console.error('[WebSocket] Error:', error);
    ws.onclose = () => console.log('[WebSocket] Closed');
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
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: true, 
        audio: true 
      });
      console.log('[WebRTC] Media stream obtained:', stream.getTracks().map(t => t.kind));
      videoRef.current.srcObject = stream;
      
      setupDeepgram(stream);

      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
        console.log('[WebRTC] Added track:', track.kind, track.label);
      });
    } catch (err) {
      console.warn('[WebRTC] Camera failed, trying audio-only:', err);
      try {
        const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioStream.getTracks().forEach(track => pc.addTrack(track, audioStream));
        alert('카메라 접근 거부됨. 음성만 사용합니다.');
      } catch (audioErr) {
        alert('마이크 접근 실패');
        throw audioErr;
      }
    }

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    console.log('[WebRTC] Sending offer to server...');

    const response = await fetch('http://localhost:8080/offer', {
      method: 'POST',
      body: JSON.stringify({
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type,
        session_id: interviewId
      }),
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`WebRTC offer failed: ${response.status}`);
    }

    const answer = await response.json();
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
    console.log('[WebRTC] Connection established successfully');
  };

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      isRecordingRef.current = false;
    } else {
      setTranscript('');
      setIsRecording(true);
      isRecordingRef.current = true;
    }
  };

  const nextQuestion = async () => {
    const answerText = transcript.trim() || "답변 없음";
    
    try {
      // Transcript 저장 (사용자 답변)
      await createTranscript(
        interview.id,
        'User',
        answerText,
        questions[currentIdx].id
      );
      
      if (currentIdx < questions.length - 1) {
        setCurrentIdx(currentIdx + 1);
        setTranscript('');
        setIsRecording(false);
      } else {
        setStep('loading');
        
        if (wsRef.current) wsRef.current.close();
        if (pcRef.current) pcRef.current.close();
        
        // 면접 완료 처리
        await completeInterview(interview.id);
        
        // 평가 리포트 대기
        setTimeout(async () => {
          try {
            const finalReport = await getEvaluationReport(interview.id);
            setReport(finalReport);
            setStep('result');
          } catch (err) {
            alert('평가 리포트 생성 중입니다. 잠시 후 다시 확인해주세요.');
            setStep('landing');
          }
        }, 10000);
      }
    } catch (err) {
      console.error('[Submit Error]:', err);
      alert('답변 제출 실패');
    }
  };

  useEffect(() => {
    if (step === 'interview' && interview && videoRef.current && !pcRef.current) {
      const initMedia = async () => {
        try {
          await setupWebRTC(interview.id);
          setupWebSocket(interview.id);
        } catch (err) {
          console.error("Media init error:", err);
        }
      };
      initMedia();
    }
  }, [step, interview]);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (pcRef.current) pcRef.current.close();
      if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
      if (deepgramConnectionRef.current) deepgramConnectionRef.current.finish();
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