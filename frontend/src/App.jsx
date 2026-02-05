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
  getCurrentUser,
  getDeepgramToken
} from './api/interview';
import { createClient } from "@deepgram/sdk";

// Layout & UI
import Header from './components/layout/Header';
import MainPage from './pages/main/MainPage';
import AuthPage from './pages/auth/AuthPage';
import LandingPage from './pages/landing/LandingPage';
import ResumePage from './pages/landing/ResumePage';
import EnvTestPage from './pages/setup/EnvTestPage';
import FinalGuidePage from './pages/landing/FinalGuidePage';
import InterviewPage from './pages/interview/InterviewPage';
import ResultPage from './pages/result/ResultPage';

function App() {
  const [step, setStep] = useState(() => sessionStorage.getItem('current_step') || 'main'); 
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');
  
  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('isDarkMode') === 'true'); // 기본: 라이트모드

  useEffect(() => {
    localStorage.setItem('isDarkMode', isDarkMode);
    if (isDarkMode) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  }, [isDarkMode]);
  
  const [account, setAccount] = useState({ 
    email: '', 
    username: '',
    password: '', 
    passwordConfirm: '',
    fullName: '', 
    birthDate: '',
    profileImage: null,
    termsAgreed: false
  });
  const [interview, setInterview] = useState(() => {
    const saved = sessionStorage.getItem('current_interview');
    return saved ? JSON.parse(saved) : null;
  });
  const [questions, setQuestions] = useState(() => {
    const saved = sessionStorage.getItem('current_questions');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentIdx, setCurrentIdx] = useState(() => {
    const saved = sessionStorage.getItem('current_idx');
    return saved ? parseInt(saved, 10) : 0;
  });
  const [report, setReport] = useState(() => {
    const saved = sessionStorage.getItem('current_report');
    return saved ? JSON.parse(saved) : null;
  });
  
  const [transcript, setTranscript] = useState('');
  const [subtitle, setSubtitle] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [userName, setUserName] = useState('');
  const [position, setPosition] = useState(() => sessionStorage.getItem('current_position') || '');
  const [resumeFile, setResumeFile] = useState(null);
  const [parsedResumeData, setParsedResumeData] = useState(() => {
    const saved = sessionStorage.getItem('current_parsed_resume');
    return saved ? JSON.parse(saved) : null;
  });

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);

  // Persistence Effect
  useEffect(() => {
    sessionStorage.setItem('current_step', step);
    sessionStorage.setItem('current_interview', JSON.stringify(interview));
    sessionStorage.setItem('current_questions', JSON.stringify(questions));
    sessionStorage.setItem('current_idx', currentIdx);
    sessionStorage.setItem('current_report', JSON.stringify(report));
    sessionStorage.setItem('current_position', position);
    sessionStorage.setItem('current_parsed_resume', JSON.stringify(parsedResumeData));
  }, [step, interview, questions, currentIdx, report, position, parsedResumeData]);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const deepgramConnectionRef = useRef(null);
  const isRecordingRef = useRef(false);
  const isInitialized = useRef(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getCurrentUser()
        .then(u => {
          setUser(u);
          // Restore the step from sessionStorage or respect the current step.
          // Only force-redirect to 'landing' if the user is on the 'auth' page while already logged in.
          const savedStep = sessionStorage.getItem('current_step');
          if (savedStep === 'auth') {
            setStep('landing');
          }
        })
        .catch(() => {
          localStorage.removeItem('token');
          setStep('main');
          isInitialized.current = true;
        });
    } else {
      // If no token, only allow 'main' or 'auth'
      const publicSteps = ['main', 'auth'];
      if (!publicSteps.includes(step)) {
        setStep('main');
      }
      isInitialized.current = true;
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
        // 로그인 시에는 username 사용
        await apiLogin(account.username, account.password);
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

        // 실제 API 호출
        await apiRegister(account.email, account.username, account.password, account.fullName);
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
    sessionStorage.clear();
    setUser(null);
    setStep('auth');
  };

  const startInterviewFlow = () => {
    if (!user) {
      alert("로그인이 필요한 서비스입니다.");
      setAuthMode('login');
      setStep('auth');
      return;
    }
    setStep('resume');
  };

  const [isLoading, setIsLoading] = useState(false);

  // ... (existing states)

  const initInterviewSession = async () => {
    setIsLoading(true);
    try {
      // 1. Create Interview with Parsed Position & User Name
      const interviewPosition = parsedResumeData?.position || position || 'General';
      
      console.log("Creating interview with:", { interviewPosition });

      const newInterview = await createInterview(interviewPosition, null, null); 
      setInterview(newInterview);

      // 2. Get Questions
      let qs = await getInterviewQuestions(newInterview.id);
      
      // Simple retry logic
      if (!qs || qs.length === 0) {
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
      // 구체적인 에러 메시지 표시
      if (err.response?.status === 401) {
          alert("세션이 만료되었습니다. 다시 로그인해주세요.");
          localStorage.removeItem('token');
          setUser(null);
          setStep('auth');
      } else {
          alert(`면접 세션 생성 실패: ${err.message || "서버 오류"}`);
      }
    } finally {
      setIsLoading(false);
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

  const setupDeepgram = async (stream) => {
    try {
      const apiKey = await getDeepgramToken();
      if (!apiKey) {
        console.warn("Deepgram API Key generation failed");
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
    } catch (err) {
      console.error("Deepgram setup failed:", err);
    }
  };

  const setupWebRTC = async (interviewId) => {
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
      body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type, session_id: interviewId }),
      headers: { 'Content-Type': 'application/json' }
    });
    const answer = await response.json();
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
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

  const finishInterview = async () => {
    setStep('loading');
    try {
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
      if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
      
      await completeInterview(interview.id);
      const res = await getEvaluationReport(interview.id);
      setReport(res);
      setStep('result');
    } catch (err) {
      console.error("Finish error:", err);
      alert('면접 종료 처리 중 오류가 발생했습니다.');
      setStep('interview');
    }
  };

  const nextQuestion = async () => {
    const answerText = transcript.trim() || "답변 내용 없음";
    try {
      await createTranscript(interview.id, 'candidate', answerText, questions[currentIdx].id);
      if (currentIdx < questions.length - 1) {
        console.log('[nextQuestion] Moving to next question index:', currentIdx + 1);
        setCurrentIdx(prev => prev + 1);
        setTranscript('');
        setIsRecording(false);
      } else {
        await finishInterview();
      }
    } catch (err) {
      alert('답변 제출에 실패했습니다.');
    }
  };

  useEffect(() => {
    if (step === 'interview' && interview && videoRef.current && !pcRef.current) {
      setupWebRTC(interview.id);
      setupWebSocket(interview.id);
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
          isInterviewing={step === 'interview'}
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
            onStartInterview={() => {
              if (user) {
                setStep('landing');
              } else {
                if (confirm("면접을 시작하려면 로그인이 필요합니다.\n로그인 페이지로 이동하시겠습니까?")) {
                  setAuthMode('login');
                  setStep('auth');
                }
              }
            }}
            onLogin={() => { setAuthMode('login'); setStep('auth'); }}
            onRegister={() => { setAuthMode('register'); setStep('auth'); }}
            user={user}
            onLogout={handleLogout}
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
          startInterview={startInterviewFlow} 
          handleLogout={handleLogout}
        />
      )}

      {step === 'resume' && (
        <ResumePage 
          onNext={() => setStep('env_test')} 
          onFileSelect={setResumeFile} 
          onParsedData={setParsedResumeData} // Pass this to save parsed info
        />
      )}
      
      {step === 'env_test' && <EnvTestPage onNext={() => setStep('final_guide')} />}
      
      {step === 'final_guide' && <FinalGuidePage onNext={initInterviewSession} onPrev={() => setStep('env_test')} isLoading={isLoading} />}

      {step === 'interview' && (
        <InterviewPage 
          currentIdx={currentIdx}
          totalQuestions={questions.length}
          question={questions[currentIdx]?.content}
          isRecording={isRecording}
          transcript={transcript}
          toggleRecording={toggleRecording}
          nextQuestion={nextQuestion}
          onFinish={finishInterview}
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