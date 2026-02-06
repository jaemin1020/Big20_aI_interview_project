import { useState, useRef, useEffect } from 'react';
import {
  createInterview,
  getInterviewQuestions,
  createTranscript,
  completeInterview,
  getEvaluationReport,
<<<<<<< HEAD
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser
=======
  uploadResume,
  getAllInterviews,
<<<<<<< HEAD
  login as apiLogin,
  register as apiRegister,
  logout as apiLogout,
  getCurrentUser
>>>>>>> b182f94287306aeafee00576932b7aef7b472b2a
=======
  login as apiLogin, 
  register as apiRegister, 
  logout as apiLogout, 
  getCurrentUser,
  getDeepgramToken
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
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
<<<<<<< HEAD

  const [account, setAccount] = useState({
    username: '',
    password: '',
    email: '',
    fullName: ''
  });

  const [interview, setInterview] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [report, setReport] = useState(null);

=======
  
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
  
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
  const [transcript, setTranscript] = useState('');
  const [subtitle, setSubtitle] = useState('');
  const [isRecording, setIsRecording] = useState(false);
<<<<<<< HEAD
  const [position, setPosition] = useState('');
<<<<<<< HEAD

=======
=======
  const [userName, setUserName] = useState('');
  const [position, setPosition] = useState(() => sessionStorage.getItem('current_position') || '');
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
  const [resumeFile, setResumeFile] = useState(null);
  const [parsedResumeData, setParsedResumeData] = useState(() => {
    const saved = sessionStorage.getItem('current_parsed_resume');
    return saved ? JSON.parse(saved) : null;
  });

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);

<<<<<<< HEAD
>>>>>>> b182f94287306aeafee00576932b7aef7b472b2a
=======
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
  
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
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
<<<<<<< HEAD
      // 0. 이력서 업로드 (있다면)
      let resumeId = null;
      if (resumeFile) {
        try {
          console.log("Uploading resume...", resumeFile.name);
          const resumeRes = await uploadResume(resumeFile);
          resumeId = resumeRes.id; // 가정: ID 반환
          console.log("Resume uploaded, ID:", resumeId);
        } catch (e) {
          if (!confirm("이력서 업로드에 실패했습니다. 이력서 없이 진행하시겠습니까?")) {
            setStep('landing'); // 취소 시 랜딩으로 복귀
            return;
          }
        }
      }

      // 1. Interview 생성
      // resume_id 등을 보낼 수 있게 API 수정이 필요할 수 있으나, 일단 position에 같이 적거나 별도 처리
      const newInterview = await createInterview(position);
      setInterview(newInterview);

      // 2. 질문 조회
      const qs = await getInterviewQuestions(newInterview.id);
      setQuestions(qs);

=======
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
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
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

<<<<<<< HEAD
  const handleRecruiterDashboard = async () => {
    try {
      const list = await getAllInterviews();
      setAllInterviews(list);
      setStep('recruiter');
    } catch (err) {
      console.error(err);
      alert("인터뷰 목록을 불러오는데 실패했습니다.");
    }
  };

  const setupWebSocket = (interviewId) => {
    const ws = new WebSocket(`ws://localhost:8080/ws/${interviewId}`);
=======
  const setupWebSocket = (sessionId) => {
    const ws = new WebSocket(`ws://localhost:8080/ws/${sessionId}`);
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'stt_result' && data.text) {
<<<<<<< HEAD
          console.log('[STT Received]:', data.text, '| Recording:', isRecordingRef.current);

=======
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
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

<<<<<<< HEAD
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

=======
      const deepgram = createClient(apiKey);
      const connection = deepgram.listen.live({
        model: "nova-2",
        language: "ko",
        smart_format: true,
        encoding: "linear16", 
        sample_rate: 16000,
      });

    connection.on("Open", () => {
      
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
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
<<<<<<< HEAD
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
=======
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (videoRef.current) videoRef.current.srcObject = stream;
      stream.getTracks().forEach(track => pc.addTrack(track, stream));
    } catch (err) { console.warn('[WebRTC] Access failed:', err); }
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1

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
<<<<<<< HEAD
    const answerText = transcript.trim() || "답변 없음";

    try {
      // Transcript 저장 (사용자 답변)
      await createTranscript(
        interview.id,
        'User',
        answerText,
        questions[currentIdx].id
      );

=======
    const answerText = transcript.trim() || "답변 내용 없음";
    try {
      await createTranscript(interview.id, 'candidate', answerText, questions[currentIdx].id);
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
      if (currentIdx < questions.length - 1) {
        console.log('[nextQuestion] Moving to next question index:', currentIdx + 1);
        setCurrentIdx(prev => prev + 1);
        setTranscript('');
        setIsRecording(false);
      } else {
<<<<<<< HEAD
        // 면접 종료
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
=======
        await finishInterview();
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
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
<<<<<<< HEAD
        <div className="card">
          <h1>{authMode === 'login' ? '로그인' : '회원가입'}</h1>
          <div className="input-group">
            {authMode === 'register' && (
              <>
                <div>
                  <label>이메일:</label>
                  <input
                    type="email"
                    value={account.email}
                    onChange={(e) => setAccount({ ...account, email: e.target.value })}
                  />
                </div>
                <div>
                  <label>성함:</label>
                  <input
                    type="text"
                    value={account.fullName}
                    onChange={(e) => setAccount({ ...account, fullName: e.target.value })}
                  />
                </div>
              </>
            )}
            <div>
              <label>아이디:</label>
              <input
                type="text"
                value={account.username}
                onChange={(e) => setAccount({ ...account, username: e.target.value })}
              />
            </div>
            <div>
              <label>비밀번호:</label>
              <input
                type="password"
                value={account.password}
                maxLength={24}
                onChange={(e) => setAccount({ ...account, password: e.target.value })}
              />
            </div>
            {authError && <p style={{ color: '#ef4444' }}>{authError}</p>}
          </div>
          <button onClick={handleAuth}>
            {authMode === 'login' ? '로그인' : '회원가입'}
          </button>
          <p
            style={{ cursor: 'pointer', color: '#3b82f6', fontSize: '0.9em' }}
            onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
          >
            {authMode === 'login' ? '회원가입' : '로그인'}
          </p>
        </div>
      )}

      {step === 'landing' && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h1>AI Interview System v2.0</h1>
            <div>
              <button onClick={handleRecruiterDashboard} style={{ fontSize: '0.8em', marginRight: '10px', backgroundColor: '#6366f1' }}>면접결과 확인</button>
              <button onClick={handleLogout} style={{ fontSize: '0.8em' }}>로그아웃</button>
            </div>
          </div>
          <p>지원 직무를 입력하고 면접을 시작하세요.</p>
          <div className="input-group">
            <div>
              <label>지원 직무:</label>
              <input
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
          <button onClick={startInterview}>면접 시작</button>
        </div>
      )}

      {step === 'recruiter' && (
        <div className="card" style={{ maxWidth: '800px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h2>Recruiter Dashboard</h2>
            <button onClick={() => setStep('landing')}>뒤로가기</button>
          </div>

          {!selectedInterviewForReview ? (
            <div className="interview-list">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #ddd', textAlign: 'left' }}>
                    <th style={{ padding: '10px' }}>ID</th>
                    <th style={{ padding: '10px' }}>지원 직무</th>
                    <th style={{ padding: '10px' }}>상태</th>
                    <th style={{ padding: '10px' }}>날짜</th>
                    <th style={{ padding: '10px' }}>작업</th>
                  </tr>
                </thead>
                <tbody>
                  {allInterviews.map((iv) => (
                    <tr key={iv.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '10px' }}>{iv.id}</td>
                      <td style={{ padding: '10px' }}>{iv.position}</td>
                      <td style={{ padding: '10px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '0.8em',
                          backgroundColor: iv.status === 'completed' ? '#d1fae5' : '#f3f4f6',
                          color: iv.status === 'completed' ? '#065f46' : '#374151'
                        }}>
                          {iv.status}
                        </span>
                      </td>
                      <td style={{ padding: '10px' }}>{new Date(iv.created_at).toLocaleDateString()}</td>
                      <td style={{ padding: '10px' }}>
                        {iv.status === 'completed' && (
                          <button
                            style={{ padding: '5px 10px', fontSize: '0.8em' }}
                            onClick={async () => {
                              const rep = await getEvaluationReport(iv.id);
                              setReport(rep);
                              setSelectedInterviewForReview(iv);
                            }}
                          >
                            결과 보기
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div>
              <button
                onClick={() => {
                  setSelectedInterviewForReview(null);
                  setReport(null);
                }}
                style={{ marginBottom: '15px', backgroundColor: '#9ca3af' }}
              >
                목록으로 돌아가기
              </button>

              {/* Reuse Result View Logic roughly */}
              {report && (
                <div className="question-box">
                  <h3>면접 결과: {selectedInterviewForReview.position} (ID: {selectedInterviewForReview.id})</h3>
                  <p>종합 점수: <strong>{report.overall_score?.toFixed(1)}/100</strong></p>
                  <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                    <h4>종합 평가</h4>
                    <p>{report.summary_text}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
=======
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
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
      )}
      
      {step === 'env_test' && <EnvTestPage onNext={() => setStep('final_guide')} />}
      
      {step === 'final_guide' && <FinalGuidePage onNext={initInterviewSession} onPrev={() => setStep('env_test')} isLoading={isLoading} />}

      {step === 'interview' && (
<<<<<<< HEAD
        <div className="card">
          <h2>실시간 면접</h2>
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
              <h3>질문 {currentIdx + 1}:</h3>
              <p>{questions[currentIdx].content}</p>

              <div style={{
                marginTop: '15px',
                padding: '10px',
                background: 'rgba(16, 185, 129, 0.1)',
                borderRadius: '8px'
              }}>
                <h4 style={{ color: '#10b981' }}>
                  🎤 {isRecording ? '녹음 중...' : '답변 준비'}
                </h4>
                <p>{transcript || '답변을 시작하려면 "녹음 시작"을 눌러주세요.'}</p>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
            <button
              onClick={toggleRecording}
              style={{ backgroundColor: isRecording ? '#ef4444' : '#10b981' }}
            >
              {isRecording ? '⏸ 녹음 중지' : '🎤 녹음 시작'}
            </button>

            <button onClick={nextQuestion}>
              {currentIdx < questions.length - 1 ? "다음 질문 ➡️" : "면접 종료 ✓"}
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
=======
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
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
      )}

      {step === 'loading' && (
        <div className="card animate-fade-in" style={{ textAlign: 'center' }}>
          <h2 className="text-gradient">AI 분석 리포트 생성 중...</h2>
          <div className="spinner" style={{ width: '60px', height: '60px', borderTopColor: 'var(--primary)' }}></div>
          <p style={{ color: 'var(--text-muted)' }}>답변 내용을 바탕으로 정밀한 결과를 도출하고 있습니다. 잠시만 기다려주세요.</p>
        </div>
      )}

<<<<<<< HEAD
      {step === 'result' && report && (
        <div className="card">
          <h2>면접 결과 분석</h2>

          <div className="question-box">
            <h3>종합 점수: {report.overall_score?.toFixed(1)}/100</h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginTop: '15px' }}>
              <div style={{ textAlign: 'center' }}>
                <p>기술 점수</p>
                <h2 style={{ color: '#3b82f6' }}>{report.technical_score?.toFixed(1)}</h2>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p>소통 능력</p>
                <h2 style={{ color: '#10b981' }}>{report.communication_score?.toFixed(1)}</h2>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p>문화 적합성</p>
                <h2 style={{ color: '#f59e0b' }}>{report.cultural_fit_score?.toFixed(1)}</h2>
              </div>
            </div>

            <div style={{ marginTop: '20px', textAlign: 'left' }}>
              <h4>종합 평가:</h4>
              <p>{report.summary_text}</p>

              {report.details_json && (
                <>
                  <h4 style={{ marginTop: '15px' }}>강점:</h4>
                  <p>{report.details_json.strengths}</p>

                  <h4 style={{ marginTop: '15px' }}>개선점:</h4>
                  <p>{report.details_json.areas_for_improvement}</p>

                  <h4 style={{ marginTop: '15px' }}>채용 추천:</h4>
                  <p>{report.details_json.recommendation}</p>
                </>
              )}
            </div>
          </div>

          <button onClick={() => setStep('landing')}>처음으로</button>
        </div>
=======
      {step === 'result' && (
        <ResultPage 
          results={report || []} 
          onReset={() => {
            setStep('landing');
            setCurrentIdx(0);
            setReport(null);
          }} 
        />
>>>>>>> e988953d21a2bc98a02bb5d025da2d98879e12e1
      )}
      </div>
    </div>
  );
}

export default App;