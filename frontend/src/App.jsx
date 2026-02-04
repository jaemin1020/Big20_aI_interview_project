import { useState, useRef, useEffect } from 'react';
import { createSession, getQuestions, submitAnswer, getResults, login as apiLogin, register as apiRegister, logout as apiLogout, getCurrentUser } from './api/interview';

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
  const [session, setSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [results, setResults] = useState([]);
  
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [userName, setUserName] = useState('');
  const [position, setPosition] = useState('');
  
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      getCurrentUser()
        .then(u => {
          setUser(u);
          setStep('landing');
          setUserName(u.full_name || u.username);
        })
        .catch(() => {
          localStorage.removeItem('token');
          setStep('auth');
        });
    }
  }, []);

  const handleAuth = async () => {
    setAuthError('');
    try {
      if (authMode === 'login') {
        // 로그인 시에는 email을 username으로 사용
        await apiLogin(account.email, account.password);
        const u = await getCurrentUser();
        setUser(u);
        setUserName(u.full_name || u.username);
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
      setAuthError(err.response?.data?.detail || '인증 실패');
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
      const sess = await createSession(userName, position);
      setSession(sess);
      const qs = await getQuestions(sess.id);
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

  const setupWebRTC = async (sessionId) => {
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
  };

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
    } else {
      setTranscript('');
      setIsRecording(true);
    }
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
  }, [step, session]);

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
            border: 'none', 
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
      
      {step === 'resume' && <ResumePage onNext={() => setStep('env_test')} />}
      
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
          results={results} 
          onReset={() => {
            setStep('landing');
            setCurrentIdx(0);
            setResults([]);
          }} 
        />
      )}
      </div>
    </div>
  );
}

export default App;
