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
import { createClient, LiveTranscriptionEvents } from "@deepgram/sdk";

function App() {
  const [step, setStep] = useState('auth');
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');
  
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
  
  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [position, setPosition] = useState('');
  const [resumeFile, setResumeFile] = useState(null);

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);
  
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const isRecordingRef = useRef(false);
  const mediaRecorderRef = useRef(null);
  const deepgramConnectionRef = useRef(null);
  const canvasRef = useRef(null);
  const [subtitle, setSubtitle] = useState(''); // 실시간 자막용

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
      } else {
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
      
      // Check if it's an authentication error
      if (err.response?.status === 401) {
        alert("인증이 만료되었습니다. 다시 로그인해주세요.");
        handleLogout();
      } else {
        const errorMsg = err.response?.data?.detail || err.message || "면접 세션 생성 실패";
        alert(errorMsg);
        setStep('landing'); // 실패 시 랜딩으로 복귀
      }
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
          
          setTranscript(prev => prev + ' ' + data.text);
        } else if (data.type === 'eye_tracking') {
             drawTracking(data.data);
        }
      } catch (err) {
        console.error('[WebSocket] Parse error:', err);
      }
    };

    ws.onerror = (error) => console.error('[WebSocket] Error:', error);
    ws.onclose = () => console.log('[WebSocket] Closed');
  };

  const setupDeepgram = async (stream) => {
    try {
      // 백엔드에서 Deepgram 토큰 가져오기 (보안 개선)
      const token = localStorage.getItem('token');
      const tokenResponse = await fetch('http://localhost:8000/stt/token', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!tokenResponse.ok) {
        throw new Error('Failed to get Deepgram token from backend');
      }

      const { api_key } = await tokenResponse.json();
      console.log('✅ Deepgram token received from backend');

      const deepgram = createClient(api_key);
      
      // AudioContext Setup with AudioWorklet (modern replacement for ScriptProcessor)
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      
      const sampleRate = audioContext.sampleRate;

      const connection = deepgram.listen.live({
        model: "nova-2",
        language: "ko",
        smart_format: true,
        encoding: "linear16",
        sample_rate: sampleRate,
      });

      connection.on(LiveTranscriptionEvents.Open, async () => {
        console.log("Deepgram WebSocket Connected");
        setSubtitle("🎤 음성 인식 준비 완료");
        
        try {
          // Load AudioWorklet module
          await audioContext.audioWorklet.addModule('/deepgram-processor.js');
          
          // Create AudioWorklet node
          const workletNode = new AudioWorkletNode(audioContext, 'deepgram-processor');
          
          // Handle messages from the worklet
          workletNode.port.onmessage = (event) => {
            // Only send if recording and connection is open
            if (!isRecordingRef.current) return;
            if (connection.getReadyState() !== 1) return;
            
            // event.data is the Int16Array buffer from the worklet
            connection.send(event.data);
          };
          
          // Connect the audio graph
          source.connect(workletNode);
          workletNode.connect(audioContext.destination);
          
          // Store worklet node for cleanup
          connection.workletNode = workletNode;
          
          // Clear success message after 2 seconds
          setTimeout(() => setSubtitle(''), 2000);
        } catch (err) {
          console.error("AudioWorklet setup failed:", err);
          alert("오디오 처리 초기화에 실패했습니다.");
        }
      });

      connection.on(LiveTranscriptionEvents.Transcript, (data) => {
        const channel = data.channel;
        if (channel && channel.alternatives && channel.alternatives[0]) {
          const transcriptText = channel.alternatives[0].transcript;
          const isFinal = data.is_final;

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

      connection.on(LiveTranscriptionEvents.Error, (err) => {
        console.error("Deepgram Error:", err);
        setSubtitle("⚠️ 음성 인식 오류 발생");
        setTimeout(() => setSubtitle(''), 3000);
        
        // 심각한 에러인 경우 사용자에게 알림
        if (err.message && err.message.includes('401')) {
          alert("음성 인식 인증에 실패했습니다. 다시 로그인해주세요.");
        }
      });

      connection.on(LiveTranscriptionEvents.Close, () => {
        console.log("Deepgram WebSocket Closed");
      });
      
      // Clean up function injection
      connection.originalFinish = connection.finish;
      connection.finish = () => {
          connection.originalFinish();
          if (connection.workletNode) {
            connection.workletNode.disconnect();
          }
          source.disconnect();
          if (audioContext.state !== 'closed') audioContext.close();
      };

      deepgramConnectionRef.current = connection;
      
    } catch (err) {
      console.error("Deepgram setup failed:", err);
      alert("음성 인식 초기화에 실패했습니다. 백엔드 연결을 확인해주세요.");
    }
  };

  const setupWebRTC = async (interviewId) => {
    console.log('[WebRTC] Starting setup for interview:', interviewId);
    const pc = new RTCPeerConnection();
    pcRef.current = pc;

    // WebRTC 연결 상태 모니터링
    pc.oniceconnectionstatechange = () => {
      console.log('[WebRTC] ICE connection state:', pc.iceConnectionState);
      if (pc.iceConnectionState === 'failed') {
        alert('비디오 연결에 실패했습니다. 네트워크를 확인하거나 페이지를 새로고침해주세요.');
      } else if (pc.iceConnectionState === 'disconnected') {
        console.warn('[WebRTC] Connection disconnected, may reconnect automatically');
      }
    };

    pc.onconnectionstatechange = () => {
      console.log('[WebRTC] Connection state:', pc.connectionState);
      if (pc.connectionState === 'failed') {
        alert('미디어 서버 연결이 끊어졌습니다.');
      }
    };

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
        
        // 오디오 전용 모드에서도 STT 활성화
        setupDeepgram(audioStream);
        
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
      {step === 'auth' && (
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
      )}

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
      )}

      {step === 'loading' && (
        <div className="card">
          <h2>AI가 평가 중입니다...</h2>
          <div className="spinner"></div>
        </div>
      )}

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
      )}
    </div>
  );
}

export default App;