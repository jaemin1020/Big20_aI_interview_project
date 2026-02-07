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
  recognizeAudio
} from './api/interview';


// Layout & UI
import Header from './components/layout/Header';
import MainPage from './pages/main/MainPage';
import LandingPage from './pages/landing/LandingPage';
import ResumePage from './pages/landing/ResumePage';
import EnvTestPage from './pages/setup/EnvTestPage';
import FinalGuidePage from './pages/landing/FinalGuidePage';
import InterviewPage from './pages/interview/InterviewPage';
import InterviewCompletePage from './pages/interview/InterviewCompletePage';
import ResultPage from './pages/result/ResultPage';
import InterviewHistoryPage from './pages/history/InterviewHistoryPage';
import AuthPage from './pages/auth/AuthPage';

// Environment variables for WebRTC/WebSocket
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8080';
const WEBRTC_URL = import.meta.env.VITE_WEBRTC_URL || 'http://localhost:8080';

function App() {
  const [step, setStep] = useState(() => {
    const saved = sessionStorage.getItem('current_step');
    const token = localStorage.getItem('token');
    if (!token && saved === 'auth') return 'main';
    return saved || 'main';
  });
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');

  const [isDarkMode, setIsDarkMode] = useState(false); // 기본: 라이트모드


  useEffect(() => {
    localStorage.setItem('isDarkMode', isDarkMode);
    console.log("Theme changed to:", isDarkMode ? "DARK" : "LIGHT");
    if (isDarkMode) {
      document.body.classList.add('dark-theme');
      document.documentElement.classList.add('dark-theme'); // html 태그에도 추가
    } else {
      document.body.classList.remove('dark-theme');
      document.documentElement.classList.remove('dark-theme');
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

  // Interview state
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
  const isRecordingRef = useRef(false);
  const isInitialized = useRef(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getCurrentUser()
        .then(u => {
          setUser(u);
          // Restore the step from sessionStorage or respect the current step.
          const savedStep = sessionStorage.getItem('current_step');

          // 1. 이미 로그인했는데 로그인/회원가입 페이지면 -> 랜딩으로
          if (savedStep === 'auth') {
            setStep('landing');
          }
          else {
            const hasInterviewData = sessionStorage.getItem('current_interview');
            const stepsRequiringInterview = ['env_test', 'final_guide', 'loading_questions', 'interview', 'loading', 'result'];

            if (stepsRequiringInterview.includes(savedStep) && !hasInterviewData) {
              console.warn("Invalid step state (missing interview data). Resetting to landing.");
              setStep('landing');
            }
          }
        })
        .catch(() => {
          localStorage.removeItem('token');
          setStep('main');
          sessionStorage.clear(); // 세션 만료 시 깔끔하게 초기화
          isInitialized.current = true;
        });
    } else {
      if (step !== 'main') {
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
        setAccount(prev => ({ ...prev, fullName: u.full_name || '' }));
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
      // 1. Create Interview with Parsed Position & Resume ID
      const interviewPosition = parsedResumeData?.structured_data?.target_position || parsedResumeData?.position || position || 'General';
      const resumeId = parsedResumeData?.id || null;

      console.log("Creating interview with:", { interviewPosition, resumeId });

      const newInterview = await createInterview(interviewPosition, null, resumeId, null);
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

  // WebSocket Setup (Eye Tracking Only - Media Server)
  // STT는 이제 REST API를 사용하므로 여기서 처리하지 않음
  const setupWebSocket = (sessionId) => {
    const ws = new WebSocket(`${WS_URL}/ws/${sessionId}`);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // if (data.type === 'stt_result') ... // Deprecated via WS

        if (data.type === 'eye_tracking') {
          drawTracking(data.data);
        }
      } catch (err) { console.error('[WS] Parse error:', err); }
    };
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
    const response = await fetch(`${WEBRTC_URL}/offer`, {
      method: 'POST',
      body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type, session_id: interviewId }),
      headers: { 'Content-Type': 'application/json' }
    });
    const answer = await response.json();
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
  };

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      setTranscript('');
      const stream = videoRef.current?.srcObject;
      if (!stream) {
        console.warn("No stream found via videoRef, trying getUserMedia");
        try {
          const newStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          startRecorder(newStream);
        } catch (e) { console.error("Mic permission error:", e); }
        return;
      }
      startRecorder(stream);
    }
  };

  const startRecorder = (stream) => {
    try {
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        console.log("Recording stopped. Processing...");
        setTranscript("답변 분석 중...");
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try {
          const result = await recognizeAudio(blob);
          console.log("STT Result:", result);
          setTranscript(result.text || "내용 없음");
        } catch (err) {
          console.error("STT Error:", err);
          setTranscript("음성 인식 오류 발생");
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (e) {
      console.error("Failed to start MediaRecorder:", e);
    }
  };


  const finishInterview = async () => {
    setStep('loading');
    try {
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
      if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }

      await completeInterview(interview.id);

      // Poll for report generation (max 30 attempts, 2 seconds interval = 60 seconds total)
      let attempts = 0;
      const maxAttempts = 30;
      const pollInterval = 2000; // 2 seconds

      const pollForReport = async () => {
        try {
          const res = await getEvaluationReport(interview.id);
          setReport(res);
          console.log('✅ Report generated successfully');
          // Stay on 'loading' step - user will click "결과 확인하기" button to proceed
        } catch (err) {
          attempts++;
          if (attempts < maxAttempts) {
            console.log(`⏳ Report not ready yet, retrying... (${attempts}/${maxAttempts})`);
            setTimeout(pollForReport, pollInterval);
          } else {
            console.error('❌ Report generation timeout');
            alert('리포트 생성 시간이 초과되었습니다. 나중에 다시 시도해주세요.');
            setStep('landing');
          }
        }
      };

      pollForReport();

    } catch (err) {
      console.error("Finish error:", err);
      alert('면접 종료 처리 중 오류가 발생했습니다.');
      setStep('interview');
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
    if (isRecording) {
      alert("답변이 기록 중입니다. 먼저 '답변 종료' 버튼을 눌러주세요.");
      return;
    }
    const answerText = transcript.trim() || "답변 내용 없음";
    try {

      await createTranscript(interview.id, 'User', answerText, questions[currentIdx].id);

      if (currentIdx < questions.length - 1) {
        console.log('[nextQuestion] Moving to next question index:', currentIdx + 1);
        setCurrentIdx(prev => prev + 1);
        setTranscript('');
        // setIsRecording(false); // Already checked
      } else {

        setStep('loading');
        // if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
        if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
        await finishInterview();

      }
    } catch (err) {
      alert('답변 제출에 실패했습니다.');
    }
  };

  // 면접 화면 초기화 (WebRTC, WebSocket)
  useEffect(() => {
    if (step === 'interview' && interview && videoRef.current && !pcRef.current) {
      setupWebRTC(interview.id);
      setupWebSocket(interview.id); // For Eye Tracking
    }
  }, [step, interview]);

  // 면접 시작 시 자동으로 녹음 시작 (Deepgram 타임아웃 방지) -> 파일 기반이므로 자동 시작 끔
  /*
  useEffect(() => {
    if (step === 'interview' && questions.length > 0 && !isRecording) {
      console.log('🎤 [AUTO] Starting recording automatically...');
      setIsRecording(true);
      isRecordingRef.current = true;
    }
  }, [step, questions]);
  */

  useEffect(() => {
    return () => {
      // if (wsRef.current) wsRef.current.close();
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
          onHistory={() => setStep('history')}
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

      <div style={{ flex: 1, width: '100%', display: 'flex', flexDirection: 'column', paddingTop: step !== 'main' && step !== 'auth' ? '80px' : '0' }}>
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
            onHistory={() => setStep('history')}
          />
        )}

        {step === 'auth' && (
          <AuthPage
            authMode={authMode}
            setAuthMode={setAuthMode}
            account={account}
            setAccount={setAccount}
            handleAuth={handleAuth}
            authError={authError}
          />
        )}

        {step === 'history' && (
          <InterviewHistoryPage
            onBack={() => setStep('landing')}
            onViewResult={(reportData) => {
              setReport(reportData);
              setStep('result');
            }}
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


        {step === 'loading_questions' && (
          <div className="card">
            <h2>AI 면접관이 질문을 준비하고 있습니다...</h2>
            <p>지원 직무와 이력서를 분석 중입니다. (AI 모델 로딩에 따라 최대 2분 소요)</p>
            <div className="spinner"></div>
          </div>
        )}

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
          <InterviewCompletePage
            isReportLoading={!report}
            onCheckResult={() => {
              if (report) {
                setStep('result');
              }
            }}
            onExit={() => {
              setStep('landing');
              setCurrentIdx(0);
              setReport(null);
            }}
          />
        )}

        {step === 'result' && (
          <ResultPage
            results={report?.details_json || []}
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