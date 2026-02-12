
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

// Layout & UI
import Header from './components/layout/Header';
import MainPage from './pages/main/MainPage';
import AuthPage from './pages/auth/AuthPage';
import LandingPage from './pages/landing/LandingPage';
import ResumePage from './pages/landing/ResumePage';
import EnvTestPage from './pages/setup/EnvTestPage';
import FinalGuidePage from './pages/landing/FinalGuidePage';
import InterviewPage from './pages/interview/InterviewPage';
import InterviewCompletePage from './pages/interview/InterviewCompletePage';
import ResultPage from './pages/result/ResultPage';
import InterviewHistoryPage from './pages/history/InterviewHistoryPage';
import AccountSettingsPage from './pages/settings/AccountSettingsPage';
import ProfileManagementPage from './pages/profile/ProfileManagementPage';
import AboutPage from './pages/about/AboutPage';


function App() {
  const [step, setStep] = useState('main');
  const [envTestStep, setEnvTestStep] = useState('audio');
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
    username: '',
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
  const [isReportLoading, setIsReportLoading] = useState(false);

  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [userName, setUserName] = useState('');
  const [position, setPosition] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [parsedResumeData, setParsedResumeData] = useState(null);

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);

  // Users selected interview for result view
  const [selectedInterview, setSelectedInterview] = useState(null);




  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const isRecordingRef = useRef(false);
  const isInitialized = useRef(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getCurrentUser()
        .then(u => {
          setUser(u);
          // 새로고침 시 저장된 상태 복구
          const savedStep = sessionStorage.getItem('app_step');
          const savedInterview = sessionStorage.getItem('app_interview');
          const savedQuestions = sessionStorage.getItem('app_questions');
          const savedCurrentIdx = sessionStorage.getItem('app_currentIdx');
          const savedReport = sessionStorage.getItem('app_report');
          const savedPosition = sessionStorage.getItem('app_position');
          const savedParsedResume = sessionStorage.getItem('app_parsedResume');

          // 상태 복구 (Hydration)
          if (savedInterview) {
            try { setInterview(JSON.parse(savedInterview)); } catch (e) { console.error(e); }
          }
          if (savedQuestions) {
            try { setQuestions(JSON.parse(savedQuestions)); } catch (e) { console.error(e); }
          }
          if (savedCurrentIdx) setCurrentIdx(Number(savedCurrentIdx));
          if (savedReport) {
            try { setReport(JSON.parse(savedReport)); } catch (e) { console.error(e); }
          }
          if (savedPosition) setPosition(savedPosition);
          if (savedParsedResume) {
            try { setParsedResumeData(JSON.parse(savedParsedResume)); } catch (e) { console.error(e); }
          }

          if (savedStep) {
            setStep(savedStep);
          } else {
            setStep('main');
          }

          isInitialized.current = true;
        })
        .catch((err) => {
          console.error("Session restore failed:", err);
          localStorage.removeItem('token');
          sessionStorage.clear();
          setStep('main');
          isInitialized.current = true;
        });
    } else {
      setStep('main');
      isInitialized.current = true;
    }
  }, []);

  // 상태 변화 시마다 sessionStorage에 저장
  useEffect(() => {
    if (!isInitialized.current || !user) return;

    sessionStorage.setItem('app_step', step);
    if (interview) sessionStorage.setItem('app_interview', JSON.stringify(interview));
    if (questions.length > 0) sessionStorage.setItem('app_questions', JSON.stringify(questions));
    sessionStorage.setItem('app_currentIdx', currentIdx.toString());
    if (report) sessionStorage.setItem('app_report', JSON.stringify(report));
    if (position) sessionStorage.setItem('app_position', position);
    if (parsedResumeData) sessionStorage.setItem('app_parsedResume', JSON.stringify(parsedResumeData));
  }, [step, user, interview, questions, currentIdx, report, position, parsedResumeData]);

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
        setStep('main');
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
  const [subtitle, setSubtitle] = useState('');

  const initInterviewSession = async () => {
    setIsLoading(true);
    setCurrentIdx(0); // 새로운 면접 시작 시 질문 인덱스 초기화
    try {
      // 1. Create Interview with Parsed Position & Resume ID
      const structuredBase = parsedResumeData?.structured_data;
      const interviewPosition = position ||
        structuredBase?.header?.target_role ||
        structuredBase?.target_position ||
        parsedResumeData?.position ||
        "보안 엔지니어";

      console.log("🚀 [Session Init] Final Position:", interviewPosition);
      console.log("🚀 [Session Init] Resume ID:", parsedResumeData?.id);

      const newInterview = await createInterview(interviewPosition, null, parsedResumeData?.id, null);
      setInterview(newInterview);

      // 2. Get Questions
      let qs = await getInterviewQuestions(newInterview.id);

      // Simple retry logic
      if (!qs || qs.length === 0) {
        console.log("Questions not ready, retrying in 3s...");
        await new Promise(r => setTimeout(r, 3000));
        qs = await getInterviewQuestions(newInterview.id);
      }

      if (!qs || qs.length === 0) {
        throw new Error("질문 생성에 시간이 걸리고 있습니다. 잠시 후 다시 시도해주세요.");
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

  const pollReport = async (interviewId) => {
    setIsReportLoading(true);
    const maxRetries = 20; // 약 1분간 시도 (3초 * 20)
    let retries = 0;

    const interval = setInterval(async () => {
      try {
        const finalReport = await getEvaluationReport(interviewId);
        if (finalReport && finalReport.length > 0) {
          setReport(finalReport);
          setIsReportLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.log("Report still generating...");
      }

      retries++;
      if (retries >= maxRetries) {
        setIsReportLoading(false);
        clearInterval(interval);
        // alert('리포트 생성 시간이 너무 오래 걸립니다. 나중에 다시 확인해주세요.');
      }
    }, 3000);
  };

  const finishInterview = async () => {
    if (wsRef.current) wsRef.current.close();
    if (pcRef.current) pcRef.current.close();

    try {
      await completeInterview(interview.id);
      setStep('complete'); // SCR-025(면접 종료 안내 화면)으로 즉시 이동
      pollReport(interview.id); // 백그라운드에서 리포트 폴링 시작
    } catch (err) {
      console.error('[Finish Error]:', err);
      alert('면접 종료 처리 중 오류가 발생했습니다.');
      setStep('landing');
    }
  };

  const nextQuestion = async () => {
    console.log('[nextQuestion] Start - Current Index:', currentIdx);
    if (!interview || !questions || !questions[currentIdx]) {
      console.error('[nextQuestion] Missing data:', { interview, questions, currentIdx });
      return;
    }
    const answerText = transcript.trim() || "답변 내용 없음";
    try {
      setIsLoading(true); // AI 질문 생성을 기다리는 동안 로딩 표시
      console.log('[nextQuestion] Saving transcript for question ID:', questions[currentIdx].id);
      await createTranscript(interview.id, 'User', answerText, questions[currentIdx].id);
      console.log('[nextQuestion] Transcript saved successfully');

      // 1. 현재 로컬 배열에 다음 질문이 있는지 확인
      if (currentIdx < questions.length - 1) {
        setCurrentIdx(prev => prev + 1);
        setTranscript('');
        setIsLoading(false);
      } else {
        // 2. 서버에서 새로운 질문이 생성되었는지 폴링 (최대 300초 대기 - LLM 생성 시간 고려)
        console.log('[nextQuestion] Polling for next AI-generated question...');
        let foundNew = false;
        for (let i = 0; i < 150; i++) { // 2초 간격으로 150번 시도 (총 300초/5분)
          await new Promise(r => setTimeout(r, 2000));
          const updatedQs = await getInterviewQuestions(interview.id);

          if (updatedQs.length > questions.length) {
            setQuestions(updatedQs);
            setCurrentIdx(prev => prev + 1);
            setTranscript('');
            foundNew = true;
            break;
          }
        }

        if (!foundNew) {
          // 더 이상 질문이 없으면 면접 종료
          console.log('[nextQuestion] No more questions found. Finishing interview.');
          setStep('loading');
          if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
          await finishInterview();
        }
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Answer submission error:', err);
      alert('답변 제출에 실패했습니다.');
      setIsLoading(false);
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
    };
  }, []);

  return (
    <div className={['interview', 'profile', 'settings'].includes(step) ? `container ${step !== 'auth' ? 'has-header' : ''}` : 'full-screen-layout'}>
      {/* Header - Visible in Most Steps */}
      {step !== 'auth' && (
        <Header
          onLogout={handleLogout}
          showLogout={!!user}
          onLogoClick={() => {
            if (step === 'interview') {
              alert("면접 진행 중에는 메인 화면으로 이동할 수 없습니다.\n면접을 종료하려면 '면접 종료' 버튼을 이용해주세요.");
              return;
            }
            setStep('main');
          }}
          isInterviewing={step === 'interview'}
          isComplete={step === 'complete'}
          onHistory={() => setStep('history')}
          onAccountSettings={() => setStep('settings')}
          onProfileManagement={() => setStep('profile')}
          onLogin={() => { setAuthMode('login'); setStep('auth'); }}
          onRegister={() => { setAuthMode('register'); setStep('auth'); }}
          pageTitle={
            step === 'history' ? '면접 이력' :
              step === 'result' ? '면접 결과' :
                step === 'settings' ? '계정 설정' :
                  step === 'profile' ? '프로필 관리' :
                    step === 'env_test' ? (envTestStep === 'audio' ? '음성 테스트' : '영상 테스트') :
                      null
          }
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
          {isDarkMode ? '☀️' : '🌑'}
        </button>
      </div>

      <div style={{
        flex: 1,
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        // 면접, 프로필, 설정 페이지를 제외한 모든 페이지에 전체 화면 강제 적용
        ...(!['interview', 'profile', 'settings'].includes(step) ? {
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100vw',
          minHeight: '100vh',
          paddingTop: '72px',
          boxSizing: 'border-box',
          zIndex: 0
        } : {})
      }}>
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
            onAbout={() => setStep('about')}
          />
        )}

        {step === 'about' && (
          <AboutPage
            onBack={() => setStep('main')}
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
            onBack={() => setStep('main')}
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
            onNext={() => { setEnvTestStep('audio'); setStep('env_test'); }}
            onFileSelect={setResumeFile}
            onParsedData={setParsedResumeData} // Pass this to save parsed info
          />
        )}
        {step === 'env_test' && (
          <EnvTestPage
            onNext={() => setStep('final_guide')}
            envTestStep={envTestStep}
            setEnvTestStep={setEnvTestStep}
          />
        )}

        {step === 'interview' && (
          <InterviewPage
            currentIdx={currentIdx}
            totalQuestions={questions.length}
            question={questions[currentIdx]?.content}
            audioUrl={questions[currentIdx]?.audio_url}
            isRecording={isRecording}
            transcript={transcript}
            toggleRecording={toggleRecording}
            nextQuestion={nextQuestion}
            onFinish={finishInterview}
            videoRef={videoRef}
            isLoading={isLoading}
          />
        )}

        {step === 'final_guide' && <FinalGuidePage onNext={initInterviewSession} onPrev={() => { setEnvTestStep('video'); setStep('env_test'); }} isLoading={isLoading} />}

        {step === 'complete' && (
          <InterviewCompletePage
            isReportLoading={isReportLoading}
            onCheckResult={() => setStep('result')}
            onExit={() => {
              setStep('main');
              setCurrentIdx(0); // 메인으로 돌아갈 때 질문 인덱스 초기화
              setReport(null);
              setIsReportLoading(false);
            }}
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
            results={report?.details_json || []}
            report={report}
            interview={selectedInterview}
            onReset={() => {
              setStep('main');
              setCurrentIdx(0);
              setReport(null);
              setSelectedInterview(null);
            }}
          />
        )}

        {step === 'history' && (
          <InterviewHistoryPage
            onBack={() => setStep('main')}
            onViewResult={(reportData, interviewData) => {
              setReport(reportData);
              setSelectedInterview(interviewData);
              setStep('result');
            }}
          />
        )}

        {step === 'settings' && (
          <AccountSettingsPage
            onBack={() => setStep('main')}
          />
        )}

        {step === 'profile' && (
          <ProfileManagementPage
            onBack={() => setStep('main')}
            user={user}
          />
        )}
      </div>
    </div>
  );
}

export default App;