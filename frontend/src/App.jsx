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
  login as apiLogin, 
  register as apiRegister, 
  logout as apiLogout, 
  getCurrentUser 
>>>>>>> main
} from './api/interview';

function App() {
  const [step, setStep] = useState('auth');
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');

  // Auth 관련 입력 상태
  const [account, setAccount] = useState({
    username: '',
    password: '',
    email: '',
    fullName: ''
  });

  const [interview, setInterview] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);

  // 결과 관련 상태
  const [report, setReport] = useState(null);
  const [results, setResults] = useState([]); // For frontend display consistency if needed

  // STT 관련 상태
  const [transcript, setTranscript] = useState(''); // 현재 질문에 대한 답변 텍스트
  const [isRecording, setIsRecording] = useState(false); // 녹음 상태
  const [fullTranscript, setFullTranscript] = useState(''); // 전체 누적 텍스트

  const [position, setPosition] = useState('');
<<<<<<< HEAD

=======
  const [resumeFile, setResumeFile] = useState(null);

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);
  
>>>>>>> main
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const isRecordingRef = useRef(false);

  // 자동 로그인 확인
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
          setStep('auth');
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
        await apiLogin(account.username, account.password);
        const u = await getCurrentUser();
        setUser(u);
        setStep('landing');
        setAccount(prev => ({ ...prev, fullName: u.full_name || '' }));
      } else {
        await apiRegister(account.email, account.username, account.password, account.accountfullName);
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

  const startInterview = async () => {
    if (!position.trim()) {
      alert("지원 직무를 입력해주세요.");
      return;
    }

    setStep('loading_questions'); // 로딩 상태 시작

    try {
      // 0. 이력서 업로드 (있다면)
      let resumeId = null;
      if (resumeFile) {
        try {
            console.log("Uploading resume...", resumeFile.name);
            const resumeRes = await uploadResume(resumeFile);
            resumeId = resumeRes.id; // 가정: ID 반환
            console.log("Resume uploaded, ID:", resumeId);
        } catch (e) {
            if(!confirm("이력서 업로드에 실패했습니다. 이력서 없이 진행하시겠습니까?")) {
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

      setStep('interview');
    } catch (err) {
      console.error("Interview start error:", err);
      alert("면접 세션 생성 실패");
      setStep('landing'); // 실패 시 랜딩으로 복귀
    }
  };

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
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] Connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'stt_result' && data.text) {
          console.log('[STT Received]:', data.text, '| Recording:', isRecordingRef.current);
          
          // 녹음 중일 때만 transcript 업데이트
          if (isRecordingRef.current) {
            setTranscript(prev => prev + ' ' + data.text);
          }
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

  // 답변 제출 및 다음 질문 이동 로직
  // 실제 API 호출이 누락되어 있어 추가합니다. (createTranscript 사용 추정)
  const submitAnswer = async (questionId, answerText) => {
    // 임시: createTranscript API를 사용하여 답변 저장 (실제 구현에 맞게 조정 필요)
    // speaker='candidate'
    await createTranscript(interview.id, 'candidate', answerText, questionId);
  };

  const nextQuestion = async () => {
    // STT로 받아온 실제 텍스트를 제출
    const answerText = transcript.trim() || "답변 내용 없음 (음성 인식 실패 또는 무응답)";

    try {
      // 1. 현재 질문에 대한 답변 제출
      await submitAnswer(questions[currentIdx].id, answerText);
      console.log(`[Submit] Question ${currentIdx + 1} answered:`, answerText);

      // 2. 화면 표시를 위한 결과 저장 (간이 저장)
      setResults(prev => [...prev, {
        question: questions[currentIdx].question_text,
        answer: answerText,
        evaluation: { status: "pending..." } // 실제 평가는 나중에 report로 받음
      }]);

      // 3. 다음 질문으로 이동 또는 종료
      if (currentIdx < questions.length - 1) {
        setCurrentIdx(currentIdx + 1);
        setTranscript('');
        setIsRecording(false);
      } else {
        // 면접 종료
        setStep('loading');

        // WebSocket 및 WebRTC 연결 종료
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        if (pcRef.current) {
          pcRef.current.close();
          pcRef.current = null;
        }

        // 전체 면접 종료 처리
        await completeInterview(interview.id);

        // AI 평가 완료 대기 후 결과 조회
        setTimeout(async () => {
          try {
            const finalReport = await getEvaluationReport(interview.id);
            setReport(finalReport);
            // 만약 서버에서 results 구조를 다르게 준다면 여기서 setResults를 갱신해야 할 수도 있음
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
    };
  }, []);

  return (
    <div className="container">
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
<<<<<<< HEAD
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h1>면접 시스템</h1>
            <button
              onClick={handleLogout}
              className="btn-secondary"
              style={{ padding: '8px 16px', fontSize: '0.85rem', margin: 0 }}
            >
              로그아웃
            </button>
=======
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h1>AI Interview System v2.0</h1>
            <div>
                <button onClick={handleRecruiterDashboard} style={{ fontSize: '0.8em', marginRight: '10px', backgroundColor: '#6366f1' }}>면접결과 확인</button>
                <button onClick={handleLogout} style={{ fontSize: '0.8em' }}>로그아웃</button>
            </div>
>>>>>>> main
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
      )}

      {step === 'interview' && (
        <div className="card">
          <h2>실시간 면접</h2>
          <video ref={videoRef} autoPlay playsInline muted />

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
          <p>지원 직무와 이력서를 분석 중입니다. (약 30초 소요)</p>
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
      )}
    </div>
  );
}

export default App;