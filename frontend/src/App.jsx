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
  const pcRef = useRef(null);
  const wsRef = useRef(null);
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
        } else if (data.type === 'eye_tracking') {
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

      await createTranscript(interview.id, 'candidate', answerText, questions[currentIdx].id);

      if (currentIdx < questions.length - 1) {
        console.log('[nextQuestion] Moving to next question index:', currentIdx + 1);
        setCurrentIdx(prev => prev + 1);
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
      setupWebSocket(interview.id);
    }
  }, [step, interview]);

  // 면접 시작 시 자동으로 녹음 시작 (Deepgram 타임아웃 방지)
  useEffect(() => {
    if (step === 'interview' && questions.length > 0 && !isRecording) {
      console.log('🎤 [AUTO] Starting recording automatically...');
      setIsRecording(true);
      isRecordingRef.current = true;
    }
  }, [step, questions]);

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
        <div className="card">
          <h1>{authMode === 'login' ? '로그인' : '회원가입'}</h1>
          <p style={{ marginBottom: '24px' }}>서비스를 이용하려면 로그인해주세요.</p>
          <div className="input-group">
            {authMode === 'register' && (
              <div>
                <label>성함</label>
                <input
                  type="text"
                  value={account.fullName}
                  onChange={(e) => setAccount({ ...account, fullName: e.target.value })}
                  placeholder="이름을 입력하세요"
                />
              </div>
            )}

            {/* 회원가입 시 Email 입력 추가 */}
            {authMode === 'register' && (
              <div>
                <label>이메일</label>
                <input
                  type="text"
                  value={account.email}
                  onChange={(e) => setAccount({ ...account, email: e.target.value })}
                  placeholder="name@example.com"
                />
              </div>
            )}

            <div>
              <label>아이디</label>
              <input
                type="text"
                value={account.username}
                onChange={(e) => setAccount({ ...account, username: e.target.value })}
                placeholder="아이디를 입력하세요"
              />
            </div>
            <div>
              <label>비밀번호</label>
              <input
                type="password"
                value={account.password}
                maxLength={24}
                onChange={(e) => setAccount({ ...account, password: e.target.value })}
                placeholder="비밀번호 (최대 24자)"
              />
            </div>
            {authError && <p className="error-message">{authError}</p>}
          </div>
          <button onClick={handleAuth} style={{ width: '100%', marginBottom: '16px' }}>
            {authMode === 'login' ? '로그인' : '회원가입'}
          </button>
          <p
            className="link-text"
            style={{ textAlign: 'center' }}
            onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
          >
            {authMode === 'login' ? '회원가입' : '로그인'}
          </p>
        </div>
      )}

      {step === 'landing' && (
        <div className="card">

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h1>면접 시스템</h1>
            <button
              onClick={handleLogout}
              className="btn-secondary"
              style={{ padding: '8px 16px', fontSize: '0.85rem', margin: 0 }}
            >
              로그아웃
            </button>
          </div>
          <p style={{ marginBottom: '24px' }}>
            {user ? `${user.full_name}님, 환영합니다!` : '환영합니다!'} <br />
            지원 정보를 입력하고 면접을 시작하세요.
          </p>
          <div className="input-group">
            <div>
              <label htmlFor="position">지원 직무</label>
              <input
                id="position"
                type="text"
                placeholder="예: Frontend 개발자"
                value={position}
                onChange={(e) => setPosition(e.target.value)}
              />
            </div>
            <div style={{ marginTop: '15px' }}>
                <label>이력서 (PDF/Word):</label>
                <input 
                    type="file" 
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setResumeFile(e.target.files[0])}
                />
                <p style={{ fontSize: '0.8em', color: '#666' }}>
                    * 이력서를 제출하면 맞춤형 면접 질문이 생성됩니다.
                </p>
            </div>
          </div>
          <button onClick={startInterview} style={{ width: '100%' }}>
            면접 시작하기
          </button>
        </div>

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

        <div className="card">
          <h2>실시간 면접</h2>

          <div style={{ position: 'relative', display: 'inline-block' }}>
            <video ref={videoRef} autoPlay playsInline muted style={{ display: 'block', maxWidth: '100%' }} />
            <canvas 
                ref={canvasRef} 
                style={{ 
                    position: 'absolute', 
                    top: 0, 
                    left: 0, 
                    pointerEvents: 'none',
                    width: '100%',
                    height: '100%'
                }} 
            />
          </div>

          <video ref={videoRef} autoPlay playsInline muted />
          
          {/* 실시간 자막 오버레이 */}
          {subtitle && (
            <div style={{
              marginTop: '-45px',
              padding: '8px 15px',
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              borderRadius: '20px',
              position: 'relative',
              textAlign: 'center',
              zIndex: 10,
              display: 'inline-block',
              maxWidth: '90%'
            }}>
              {subtitle}
            </div>
          )}
          

          {questions.length > 0 && (
            <div className="question-box">
              <h3>질문 {currentIdx + 1}</h3>
              <p style={{ color: '#1a1a2e', fontSize: '1rem', lineHeight: '1.6' }}>
                {questions[currentIdx].question_text}
              </p>

              {/* 실시간 STT 전사 텍스트 표시 */}
              <div className="transcript-box">
                <h4>
                  {isRecording ? '🎤 녹음 중...' : '📝 답변 준비'}
                </h4>
                <p style={{ margin: 0, fontSize: '0.95rem', color: '#1a1a2e' }}>
                  {transcript || '답변을 시작하려면 "녹음 시작" 버튼을 눌러주세요.'}
                </p>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '20px' }}>
            <button
              onClick={toggleRecording}
              className={isRecording ? 'btn-stop' : 'btn-record'}
              style={{ minWidth: '130px' }}
            >
              {isRecording ? '⏸ 녹음 중지' : '🎤 녹음 시작'}
            </button>

            <button
              onClick={nextQuestion}
              disabled={!transcript.trim() && isRecording}
              style={{ minWidth: '130px' }}
            >
              {currentIdx < questions.length - 1 ? "다음 질문 →" : "면접 종료 ✓"}
            </button>
          </div>
        </div>
      )}

      {step === 'loading_questions' && (
        <div className="card">
          <h2>AI 면접관이 질문을 준비하고 있습니다...</h2>
          <p>지원 직무와 이력서를 분석 중입니다. (AI 모델 로딩에 따라 최대 2분 소요)</p>
          <div className="spinner"></div>
        </div>
      )}

      {step === 'loading' && (
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>답변을 분석 중입니다</h2>
          <div className="spinner"></div>
        </div>
      )}

      {step === 'result' && report && (
        <div className="card">
          <h2>면접 결과</h2>
          {/* report.results가 있다면 그것을 사용하고, 없다면 프론트 state인 results 사용 (구조에 따라 다름) */}
          {(report.details || results).map((r, i) => (
            <div key={i} className="result-item">
              <strong style={{ color: '#1a1a2e' }}>Q: {r.question_text || r.question}</strong>
              <p style={{ marginTop: '8px' }}>A: {r.answer_text || r.answer}</p>
              <div className="result-evaluation">
                <h4 style={{ color: '#2563eb', margin: '0 0 12px 0', fontSize: '0.95rem' }}>피드백</h4>
                <pre>
                  {/* JSON 파싱이 필요할 수 있음 */}
                  {typeof r.evaluation === 'string' ? r.evaluation : JSON.stringify(r.evaluation, null, 2)}
                </pre>
                <h4 style={{ color: '#059669', margin: '16px 0 8px 0', fontSize: '0.95rem' }}>감정 분석</h4>
                <p style={{ margin: 0 }}>
                  {r.emotion_data ? `주요 감정: ${r.emotion_data.dominant_emotion}` : "분석 대기 중..."}
                </p>
              </div>
            </div>
          ))}
          <button onClick={() => setStep('landing')} style={{ width: '100%', marginTop: '16px' }}>
            처음으로
          </button>
        </div>

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