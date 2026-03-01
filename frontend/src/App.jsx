
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
import RecruiterMainPage from './pages/recruiter/RecruiterMainPage';
import JobPostingCreatePage from './pages/recruiter/JobPostingCreatePage';


function App() {
  const [step, setStep] = useState('main');
  const [envTestStep, setEnvTestStep] = useState('audio');
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [authError, setAuthError] = useState('');

  // 프로필 페이지 이탈 가드
  const [profileDirty, setProfileDirty] = useState(false);
  const [pendingStep, setPendingStep] = useState(null);
  const [showProfileLeaveModal, setShowProfileLeaveModal] = useState(false);
  // 프로필 페이지에서 저장 함수를 바인딩하는 ref
  const profileSaveRef = useRef(null);

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
  const [isMediaReady, setIsMediaReady] = useState(false); // 장비 준비 상태 추가

  const [transcript, setTranscript] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [userName, setUserName] = useState('');
  const [position, setPosition] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [parsedResumeData, setParsedResumeData] = useState(null);
  const [visionData, setVisionData] = useState(null); // [NEW] Vision Analysis Data
  // [Fix] 답변 완료 상태 추적 (타이머 정지 및 버튼 교체용)
  const [isAnswerFinished, setIsAnswerFinished] = useState(false);
  const isAnswerFinishedRef = useRef(false);
  // [Fix] STT 최종 확정 상태 (상태로 관리하여 UI 연동)
  const [isTranscriptLocked, setIsTranscriptLocked] = useState(false);
  const [isSttProcessing, setIsSttProcessing] = useState(false); // [신규] STT 서버 처리 중 상태
  const finalizeTimeoutRef = useRef(null);

  // Recruiter State
  const [allInterviews, setAllInterviews] = useState([]);
  const [selectedInterviewForReview, setSelectedInterviewForReview] = useState(null);

  // Users selected interview for result view
  const [selectedInterview, setSelectedInterview] = useState(null);

  // Recruiter Navigation State (Lifted for Logo Reset)
  const [recruiterMenu, setRecruiterMenu] = useState('dashboard');




  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const wsRef = useRef(null);
  const aiStreamWsRef = useRef(null); // AI 질문 스트리밍용 WS
  const currentIdxRef = useRef(0); // stale closure 방지용 : currentIdx 최신값 동기화
  const mediaRecorderRef = useRef(null);
  const isRecordingRef = useRef(false);

  const isInitialized = useRef(false);
  // [수정] 클로저 stale 문제 해결: transcript 최신값을 ref로 항상 동기화
  const liveTranscriptRef = useRef('');

  // 프로필 페이지에서 동작 중 이탈 시 다른 step으로 안전하게 이동
  const navigateSafe = (targetStep, force = false) => {
    if (!force && step === 'profile' && profileDirty) {
      setPendingStep(targetStep);
      setShowProfileLeaveModal(true);
    } else {
      setStep(targetStep);
      if (force) setProfileDirty(false); // 강제 이동 시 dirty 상태도 초기화
    }
  };

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
          if (savedCurrentIdx) {
            const idx = Number(savedCurrentIdx);
            setCurrentIdx(idx);
            // 초기 복구 시에도 필요하다면 서버에 알림
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ type: 'next_question', index: idx }));
            }
          }
          if (savedReport) {
            try { setReport(JSON.parse(savedReport)); } catch (e) { console.error(e); }
          }
          if (savedPosition) setPosition(savedPosition);
          if (savedParsedResume) {
            try { setParsedResumeData(JSON.parse(savedParsedResume)); } catch (e) { console.error(e); }
          }

          if (savedStep) {
            setStep(savedStep);
            // [추가] 새로고침 시 최신 질문 정보(TTS URL 등)를 서버에서 다시 가져와 세션 스토리지의 Stale 데이터 갱신
            if (savedInterview) {
              const interviewObj = JSON.parse(savedInterview);
              getInterviewQuestions(interviewObj.id)
                .then(data => {
                  if (data.questions && data.questions.length > 0) {
                    setQuestions(data.questions);
                    console.log("🔄 [Hydration] Questions updated from server");
                  }
                })
                .catch(err => console.error("Failed to re-fetch questions during hydration:", err));
            }
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

  // transcript 상태 → ref 동기화 (onstop 클로저 stale 방지)
  useEffect(() => {
    liveTranscriptRef.current = transcript;
  }, [transcript]);

  // currentIdx 상태 → ref 동기화 (AI 스트리밍 클로저 stale 방지)
  useEffect(() => {
    currentIdxRef.current = currentIdx;
  }, [currentIdx]);

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
      const usernameRegex = /^[a-z0-9]{4,12}$/;
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!usernameRegex.test(account.username)) {
        setAuthError("아이디는 4~12자의 영문 소문자, 숫자만 가능합니다. (공백/특수문자 불가)");
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

        // 사용자 권한에 따라 다른 페이지로 이동
        if (u.role === 'recruiter' || u.role === 'admin') {
          setStep('recruiter_main'); // 관리자 전용 페이지
        } else {
          setStep('main'); // 일반 사용자 페이지
        }

        setAccount(prev => ({ ...prev, fullName: u.full_name || '' }));
      } else {
        // 회원가입 검증
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(account.email)) {
          setAuthError('올바른 이메일 형식이 아닙니다.');
          return;
        }

        if (account.password.length < 8) {
          setAuthError('비밀번호는 최소 8자 이상이어야 합니다.');
          return;
        }

        if (account.password !== account.passwordConfirm) {
          setAuthError('비밀번호가 일치하지 않습니다.');
          return;
        }

        if (!account.fullName) {
          setAuthError('이름을 입력해주세요.');
          return;
        }

        if (!account.birthDate) {
          setAuthError('생년월일을 입력해주세요.');
          return;
        }

        if (!account.termsAgreed) {
          setAuthError('이용약관에 동의해야 합니다.');
          return;
        }

        // 실제 API 호출 (생년월일, 프로필 이미지 포함)
        await apiRegister(
          account.email,
          account.username,
          account.password,
          account.fullName,
          account.birthDate,
          account.profileImage
        );
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

  const [subtitle, setSubtitle] = useState('');

  const initInterviewSession = async () => {
    setIsLoading(true);
    setIsMediaReady(false); // 새 세션 시작 시 상태 리셋
    setCurrentIdx(0); // 새로운 면접 시작 시 질문 인덱스 초기화
    setIsAnswerFinished(false); // 답변 상태 초기화
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

      // 2. Get Questions (백엔드 커밋 시간을 위해 2초 대기 후 첫 요청)
      await new Promise(r => setTimeout(r, 2000));
      let data = await getInterviewQuestions(newInterview.id);
      console.log("🚀 [Session Init] Initial Data received:", data);
      let qs = data.questions || [];

      // Simple retry logic (최대 5번 재시도)
      let retryCount = 0;
      // [개선] 질문 개수뿐만 아니라, 첫 번째 질문의 TTS URL이 준비되었는지도 함께 체크 (기계음 방지)
      while (retryCount < 5) {
        const firstQHasAudio = qs.length > 0 && qs[0].audio_url;

        if (qs.length > 0 && firstQHasAudio) {
          break; // 질문이 있고 음성 주소도 준비됨
        }

        console.log(`Questions or Audio not ready (attempt ${retryCount + 1}), retrying in 5s...`);
        await new Promise(r => setTimeout(r, 5000));
        data = await getInterviewQuestions(newInterview.id);
        qs = data.questions || [];
        retryCount++;
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
        const errorDetail = err.response?.data?.detail || err.message || "서버 오류";
        console.error("🚀 [Detailed Error]:", err.response?.data);
        alert(`면접 세션 생성 실패: ${errorDetail}`);
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
        if (data.type === 'stt_processing') {
          // [신규] 서버에서 STT 처리가 시작됨을 알림
          if (data.index === currentIdxRef.current) {
            setIsSttProcessing(true);
            isSttProcessingRef.current = true;
            console.log(`[STT Status] Processing for Index ${data.index}...`);
          }
        } else if (data.type === 'stt_result' && data.text) {
          const newText = data.text.trim();
          const sttIdx = data.index !== undefined ? data.index : recordingIdxRef.current;
          console.log('[STT Received]:', newText, 'for Index:', sttIdx, 'Current:', currentIdxRef.current);

          setIsSttProcessing(false); // 결과가 오면 처리 중 상태 해제
          isSttProcessingRef.current = false;

          setTranscript(_ => {
            // [Fix 1] 세션 가드
            // [Fix 2] 다음 질문 인터뷰 로딩 중(isLoading)에도 차단
            const isIndexMismatch = (sttIdx !== -1 && sttIdx !== currentIdxRef.current);
            const isLocked = isTranscriptLockedRef.current;

            if (isLoadingRef.current || isIndexMismatch || isLocked) {
              console.warn(`[STT Ignored] Guard: Loading=${isLoadingRef.current}, IndexMatch=${!isIndexMismatch} (${sttIdx} vs ${currentIdxRef.current}), Locked=${isLocked}`);
              return liveTranscriptRef.current;
            }

            if (liveTranscriptRef.current.endsWith(newText)) return liveTranscriptRef.current;

            const updated = liveTranscriptRef.current ? `${liveTranscriptRef.current} ${newText}` : newText;

            // [중요] Ref를 먼저 업데이트하고 리턴하여 상태 동기화 불일치 원천 차단
            liveTranscriptRef.current = updated;

            // [추가] 답변 종료(Stop) 상태에서 결과가 오면 즉시 확정 (또는 약간의 딜레이 후 확정)
            if (isAnswerFinishedRef.current) {
              console.log("[STT Finalizing] Result arrived after Stop Answer. Unlocking & Re-locking.");
              // 잠금을 잠시 풀고 최신 텍스트로 다시 확정
              setIsTranscriptLocked(true);
              isTranscriptLockedRef.current = true;
              isAcceptingSTTRef.current = false;

              // [핵심] 결과가 왔으므로 DB 저장 시도 (강제 저장)
              const currentInterview = interviewRef.current;
              const currentQuestions = questionsRef.current;
              const targetQuestion = currentQuestions[currentIdxRef.current];

              if (currentInterview && targetQuestion) {
                console.log("[STT Background Save] Final transcript arrived. Saving to DB...");
                createTranscript(currentInterview.id, 'User', updated, targetQuestion.id)
                  .then(() => {
                    isTranscriptSavedRef.current = true;
                    console.log("[STT Background Save] Success for Index:", currentIdxRef.current);
                  })
                  .catch(e => console.error("[STT Background Save] Error:", e));
              } else {
                console.warn("[STT Background Save] Skipped: Interview or Question not found in Ref.");
              }
            }

            return updated;
          });
        } else if (data.type === 'vision_analysis') {
          // [NEW] Update Vision Data State
          setVisionData(data.data);
        }
      } catch (err) {
        console.error('[WebSocket] Parse error:', err);
      }
    };

    ws.onerror = (error) => console.error('[WebSocket] Error:', error);
    ws.onclose = () => console.log('[WebSocket] Closed');
  };


  const setupAiStreamWebSocket = (interviewId) => {
    // 백엔드 코어(8000)의 스트리밍 채널에 연결
    const ws = new WebSocket(`ws://localhost:8000/interviews/ws/${interviewId}`);
    aiStreamWsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ai_token' && data.token) {
          const token = data.token;

          setQuestions(prev => {
            // currentIdxRef.current 로 항상 최신 인덱스 참조 (stale closure 방지)
            // 생성되는 건 '다음 질문'이므로 현재 인덱스 + 1 자리에 스트리밍
            const nextSlot = currentIdxRef.current + 1;
            const newQs = [...prev];

            // 다음 질문 슬롯이 아직 없으면 스트리밍용 빈 객체 생성
            if (!newQs[nextSlot]) {
              newQs[nextSlot] = { id: `streaming_${Date.now()}`, content: '', isStreaming: true };
            }

            // 토큰 이어붙이기
            const existing = newQs[nextSlot].content || '';
            newQs[nextSlot] = {
              ...newQs[nextSlot],
              content: existing + token,
              isStreaming: true
            };
            return newQs;
          });
        }
      } catch (err) {
        console.error('[AI Stream WS] Parse error:', err);
      }
    };

    ws.onerror = (err) => console.error('[AI Stream WS] Error:', err);
    ws.onclose = () => console.log('[AI Stream WS] Closed');
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
      console.log('[WebRTC] Media stream obtained:', stream.getTracks().map(t => ({ kind: t.kind, label: t.label })));

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        console.log('[WebRTC] Local video srcObject set.');
      } else {
        console.warn('[WebRTC] videoRef.current is missing during stream setup!');
      }

      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
        console.log('[WebRTC] Added track to PC:', track.kind, track.label);
      });
    } catch (err) {
      console.error('[WebRTC] navigator.mediaDevices.getUserMedia FAILED:', err);
      try {
        const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('[WebRTC] Audio-only stream obtained.');
        audioStream.getTracks().forEach(track => pc.addTrack(track, audioStream));
        if (videoRef.current) {
          videoRef.current.srcObject = audioStream;
        }
        alert('카메라를 인식할 수 없거나 권한이 거부되었습니다. 음성으로만 면접을 진행합니다.');
      } catch (audioErr) {
        console.error('[WebRTC] Audio-only also FAILED:', audioErr);
        alert('마이크와 카메라를 모두 인식할 수 없습니다. 장비 연결을 확인하고 브라우저 권한을 허용해 주세요.');
        throw audioErr;
      }
    }

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    // ICE Wait (Timeout added)
    console.log('[WebRTC] Waiting for ICE gathering (Current state:', pc.iceGatheringState, ')');
    await new Promise((resolve) => {
      if (pc.iceGatheringState === 'complete') { resolve(); return; }
      const checkState = () => {
        console.log('[WebRTC] ICE Gathering State Change:', pc.iceGatheringState);
        if (pc.iceGatheringState === 'complete') {
          pc.removeEventListener('icegatheringstatechange', checkState);
          resolve();
        }
      };
      pc.addEventListener('icegatheringstatechange', checkState);
      setTimeout(() => {
        console.warn('[WebRTC] ICE gathering timed out (1.5s)');
        pc.removeEventListener('icegatheringstatechange', checkState);
        resolve();
      }, 1500);
    });

    console.log('[WebRTC] Sending offer to media-server...');
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
      const errorText = await response.text();
      console.error('[WebRTC] Offer fetch error:', response.status, errorText);
      throw new Error(`WebRTC offer failed: ${response.status}`);
    }

    const answer = await response.json();
    console.log('[WebRTC] Received Answer SDP from server.');
    await pc.setRemoteDescription(new RTCSessionDescription(answer));
    console.log('[WebRTC] WebRTC connection handshake complete.');
    setIsMediaReady(true);
  };

  // [Fix] STT 최종 확정을 위한 디바운스 함수
  const resetFinalizeTimer = () => {
    if (finalizeTimeoutRef.current) {
      clearTimeout(finalizeTimeoutRef.current);
    }
    // [Fix] 문장이 길거나 지연이 있을 수 있으므로 여유롭게 2.5초간 침묵 시 최종 확정
    finalizeTimeoutRef.current = setTimeout(async () => {
      // [신규] 서버에서 아직 STT 분석 중이라면 확정하지 않고 더 기다림 (Recursive check)
      if (isSttProcessingRef.current) {
        console.log('[STT Lock Delayed] Server is still processing. Waiting 2s more...');
        resetFinalizeTimer();
        return;
      }

      if (isLoadingRef.current) return;

      setIsTranscriptLocked(true);
      isTranscriptLockedRef.current = true; // Ref 동기화 (WS 핸들러용)
      isAcceptingSTTRef.current = false;    // 이제 이 질문에 대한 STT는 더 이상 수신 안 함
      setIsSttProcessing(false);            // 타임아웃 종료 시 처리 상태도 강제 해제

      if (!liveTranscriptRef.current.trim()) {
        // [수정] 정말로 답변이 없는지 최종 확인 (서버 분석 중이면 더 기다림)
        if (isSttProcessingRef.current) {
          console.log('[STT Lock Delayed] Server is still processing. Skipping "No Content" lock.');
          resetFinalizeTimer();
          return;
        }
        setTranscript('답변 내용 없음');
        liveTranscriptRef.current = '답변 내용 없음';
      }
      console.log('[STT Locked] Final Transcript:', liveTranscriptRef.current);

      // [핵심 추가] 확정 즉시 DB 저장 시도 (Auto-Save)
      const currentInterview = interviewRef.current;
      const currentQuestions = questionsRef.current;
      const targetQuestion = currentQuestions[currentIdxRef.current];

      if (!isTranscriptSavedRef.current && currentInterview && targetQuestion) {
        try {
          console.log('[STT Auto-Save] Saving transcript for Index:', currentIdxRef.current);
          console.log('[STT Auto-Save] Payload:', {
            interviewId: currentInterview.id,
            speaker: 'User',
            text: liveTranscriptRef.current,
            questionId: targetQuestion.id
          });
          await createTranscript(currentInterview.id, 'User', liveTranscriptRef.current, targetQuestion.id);
          isTranscriptSavedRef.current = true;
          console.log('[STT Auto-Save] Transcript saved successfully');
        } catch (e) {
          console.error('[STT Auto-Save] Failed to save transcript:', e);
        }
      } else {
        console.log('[STT Auto-Save] Skipped: isTranscriptSaved=', isTranscriptSavedRef.current);
      }
    }, 2500);
  };

  const toggleRecording = async () => {
    if (isRecording) {
      console.log('[STT] Stopping recording...');

      // WebSocket으로 녹음 중지 알림 (media server에게 오디오 분석 비활성화 시그널)
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'stop_recording' }));
      }

      setIsRecording(false);
      isRecordingRef.current = false;
      setIsAnswerFinished(true); // 답변 종료 상태로 전환
      isAnswerFinishedRef.current = true;

      // [Fix] Debounce 방식으로 최종 확정 시작
      resetFinalizeTimer();
    } else {
      // 녹음 시작
      if (!isMediaReady) {
        alert('장비가 아직 준비되지 않았습니다. 잠시만 기다려주세요.');
        return;
      }
      console.log('[STT] Starting recording for index:', currentIdx);
      setTranscript('');
      liveTranscriptRef.current = '';
      setIsRecording(true);
      isRecordingRef.current = true;
      isAcceptingSTTRef.current = true;     // STT 수신 시작
      recordingIdxRef.current = currentIdx; // 현재 질문 인덱스 고정
      setIsSttProcessing(false); // 녹음 시작 시 상태 초기화
      isTranscriptSavedRef.current = false; // 새 녹음 시작 시 저장 상태 초기화

      // WebSocket으로 녹음 시작 알림 (인덱스 포함)
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'start_recording', index: currentIdx }));
      }
    }

    console.log('[toggleRecording] New state will be:', {
      isRecording: !isRecording,
      transcript: isRecording ? transcript : ''
    });
  };

  const pollReport = async (interviewId) => {
    setIsReportLoading(true);
    // [버그1 수정] maxRetries 40번(120초)으로 연장. LLM 최종 리포트는 최대 2분 소요 가능
    const maxRetries = 40;
    let retries = 0;

    const interval = setInterval(async () => {
      if (reportAbortControllerRef.current) reportAbortControllerRef.current.abort();
      reportAbortControllerRef.current = new AbortController();

      try {
        const finalReport = await getEvaluationReport(interviewId, reportAbortControllerRef.current.signal);
        // [버그1 수정] id=0은 백엔드가 "아직 생성 중"일 때 반환하는 임시 응답.
        // id가 1 이상인 경우에만 실제 DB에 저장된 리포트로 인식
        if (finalReport && finalReport.id > 0) {
          setReport(finalReport);
          setIsReportLoading(false);
          clearInterval(interval);
          console.log('✅ [pollReport] 리포트 생성 완료 (id:', finalReport.id, ')');
        } else {
          console.log(`🔄 [pollReport] 아직 생성 중... (retry: ${retries + 1}/${maxRetries})`);
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.warn("[pollReport] API 오류, 재시도 중...", err?.response?.status);
      }

      retries++;
      if (retries >= maxRetries) {
        setIsReportLoading(false);
        clearInterval(interval);
        console.warn('[pollReport] 최대 재시도 횟수 초과. 폴링 종료.');
      }
    }, 5000); // 5초 간격으로 상향 (서버 부하 감소)
  };

  const finishInterview = async () => {
    // 0. 마지막 답변이 저장되지 않았다면 저장 시도
    const currentInterview = interviewRef.current;
    const currentQuestions = questionsRef.current;
    const targetQuestion = currentQuestions[currentIdxRef.current];

    if (!isTranscriptSavedRef.current && liveTranscriptRef.current.trim() && currentInterview && targetQuestion) {
      try {
        console.log('[finishInterview] Saving final transcript before finish.');
        await createTranscript(currentInterview.id, 'User', liveTranscriptRef.current.trim(), targetQuestion.id);
        isTranscriptSavedRef.current = true;
        console.log('[finishInterview] Final transcript saved.');
      } catch (e) {
        console.warn('[finishInterview] Failed to save final transcript:', e);
      }
    }

    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }

    try {
      if (currentInterview) {
        await completeInterview(currentInterview.id);
        setStep('complete'); // SCR-025(면접 종료 안내 화면)으로 즉시 이동
        pollReport(currentInterview.id); // 백그라운드에서 리포트 폴링 시작
      }
    } catch (err) {
      console.error('[Finish Error]:', err);
      alert('면접 종료 처리 중 오류가 발생했습니다.');
      setStep('landing');
    }
  };



  useEffect(() => {
    // 인터뷰 중이고, 현재 질문은 있는데 audio_url이 없는 경우에만 실행
    const currentQuestion = questionsRef.current[currentIdx];
    if (step !== 'interview' || !interview || !currentQuestion || currentQuestion.audio_url) return;

    const interval = setInterval(async () => {
      if (ttsAbortControllerRef.current) ttsAbortControllerRef.current.abort();
      ttsAbortControllerRef.current = new AbortController();

      console.log(`🔄 [TTS Polling] Fetching audio URL for Question index ${currentIdx + 1}...`);
      try {
        const data = await getInterviewQuestions(interview.id, ttsAbortControllerRef.current.signal);
        const updatedQs = data.questions || [];

        // 현재 인덱스의 질문에 오디오 URL이 생겼는지 확인
        if (updatedQs[currentIdx]?.audio_url) {
          console.log(`✅ [TTS Polling] Audio URL found: ${updatedQs[currentIdx].audio_url}`);
          setQuestions(updatedQs);
          clearInterval(interval);
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error("[TTS Polling] Failed to fetch questions:", err);
      }
    }, 5000); // 5초 간격으로 상향 (서버 부하 감소)

    return () => {
      clearInterval(interval);
      if (ttsAbortControllerRef.current) ttsAbortControllerRef.current.abort();
    };
  }, [step, currentIdx, interview]); // questions 제거: 타임스탬프 변경에 의한 불필요한 재실행 방지

  const nextQuestion = async () => {
    // [Fix 1] 질문 전환 시작 즉시 이전 답변의 모든 STT 수신을 강제로 차단하여 오염 방지
    isAcceptingSTTRef.current = false;
    isTranscriptLockedRef.current = true;

    const answerText = liveTranscriptRef.current.trim();
    const currentInterview = interviewRef.current;
    const currentQuestions = questionsRef.current;
    const targetQuestion = currentQuestions[currentIdxRef.current];

    console.log('[nextQuestion] START - ID:', targetQuestion?.id, 'Answer:', answerText.substring(0, 30));
    if (!currentInterview || !currentQuestions || !targetQuestion) {
      console.error('[nextQuestion] Missing data from Refs:', { currentInterview, currentQuestions, targetQuestion });
      return;
    }
    try {
      setIsLoading(true); // AI 질문 생성을 기다리는 동안 로딩 표시

      // [Fix] 이미 자동 저장되지 않은 경우에만 저장 시도
      if (!isTranscriptSavedRef.current) {
        console.log('[nextQuestion] Manual saving transcript for question ID:', targetQuestion.id);
        await createTranscript(currentInterview.id, 'User', answerText || '답변 내용 없음', targetQuestion.id);
        isTranscriptSavedRef.current = true;
        console.log('[nextQuestion] Transcript saved successfully');
      } else {
        console.log('[nextQuestion] Transcript already saved by Auto-Save, skipping manual save');
      }

      // 1. 현재 로컬 배열에 다음 질문이 있는지 확인
      if (currentIdx < questions.length - 1) {
        // [추가/수정] 미리 생성된 다음 질문(2번 등)의 최신 정보(특히 audio_url)를 서버에서 다시 가져옴
        const freshData = await getInterviewQuestions(interview.id);
        if (freshData.questions && freshData.questions.length > 0) {
          setQuestions(freshData.questions);
        }

        const nextIdx = currentIdx + 1;
        setCurrentIdx(nextIdx);
        setTranscript('');
        liveTranscriptRef.current = '';
        setIsAnswerFinished(false);
        isAnswerFinishedRef.current = false;
        setIsTranscriptLocked(false);
        isTranscriptLockedRef.current = false; // 잠금 해제
        isTranscriptSavedRef.current = false; // 저장 상태 초기화
        recordingIdxRef.current = -1; // 질문 전환 시 녹음 매칭 인덱스 초기화
        setIsLoading(false);

        // WebSocket으로 질문 전환 알림
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'next_question', index: nextIdx }));
        }
      } else {
        // 2. 서버에서 새로운 질문이 생성되었는지 폴링 (최대 300초 대기)
        console.log('[nextQuestion] Polling for next AI-generated question...');
        let foundNew = false;
        for (let i = 0; i < 60; i++) { // 2초 간격으로 60번 시도 (최대 2분으로 단축)
          if (nextQAbortControllerRef.current) nextQAbortControllerRef.current.abort();
          nextQAbortControllerRef.current = new AbortController();

          await new Promise(r => setTimeout(r, 5000)); // 5초 간격 (서버 부하 감소)
          try {
            const data = await getInterviewQuestions(interview.id, nextQAbortControllerRef.current.signal);
            const updatedQs = data.questions || [];
            const currentStatus = data.status;

            // [핵심] 서버에서 면접이 종료되었다고 알려주면 즉시 루프 탈출
            if (currentStatus === 'COMPLETED') {
              console.log('[nextQuestion] Server signaled COMPLETED status. Finalizing.');
              setQuestions(updatedQs);
              foundNew = false; // 더 이상의 질문은 없음
              break;
            }

            const lastQId = questions.length > 0 ? questions[questions.length - 1].id : null;
            const newLastQId = updatedQs.length > 0 ? updatedQs[updatedQs.length - 1].id : null;

            if (updatedQs.length > questions.length || (newLastQId !== null && newLastQId !== lastQId)) {
              const nextIdx = questions.length; // 새로 추가된 질문의 인덱스

              // [수정] audio_url 기다리지 않고 질문 텍스트 즉시 표시 (TTS는 백그라운드에서 생성됨)
              console.log("✅ [Next Question] New question ready. Showing immediately.");
              setQuestions(updatedQs);
              setCurrentIdx(prev => prev + 1);
              setTranscript('');
              foundNew = true;

              // WebSocket으로 신규 질문 전환 알림
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'next_question', index: nextIdx }));
              }
              break;
            }
          } catch (err) {
            if (err.name === 'AbortError') continue;
            console.error('Next question polling error:', err);
          }
        } // end for loop

        if (!foundNew) {
          // [수정] 폴링 타임아웃 시 무조건 종료하지 않고, 서버 상태가 COMPLETED일 때만 자동 종료
          const finalCheck = await getInterviewQuestions(interview.id);
          if (finalCheck.status === 'COMPLETED') {
            console.log('[nextQuestion] Server confirmed COMPLETED. Finishing.');
            setStep('loading');
            if (pcRef.current) { pcRef.current.close(); pcRef.current = null; }
            await finishInterview();
          } else {
            console.warn('[nextQuestion] Polling timed out but interview not marked as COMPLETED by server.');
            alert('AI 면접관의 다음 질문 생성이 지연되고 있습니다. 잠시 후 다시 [다음 질문] 버튼을 눌러주세요.');
          }
        }
        setIsLoading(false);
      } // end else block
    } catch (err) {
      console.error('Answer submission error:', err);
      alert('답변 제출에 실패했습니다.');
      setIsLoading(false);
    }
  };

  // [Fix 1] 타이머 종료 핸들러 — InterviewPage의 onTimerEnd prop으로 연결
  // wasRecording=true: 녹음을 멈추고 STT 완료 후 자동으로 nextQuestion 호출
  // wasRecording=false: 즉시 nextQuestion 호출
  const handleTimerEnd = (wasRecording) => {
    if (wasRecording) {
      console.log('[TimerEnd] 녹음 중 시간 초과 → 답변 종료 처리');
      // 녹음 중지 시그널 전송
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'stop_recording' }));
      }
      setIsRecording(false);
      isRecordingRef.current = false;
      setIsAnswerFinished(true); // 답변 종료 상태로 전환
      isAnswerFinishedRef.current = true;

      // [Fix] Debounce 방식으로 최종 확정 시작
      resetFinalizeTimer();
    } else {
      console.log('[TimerEnd] 녹음 없이 시간 초과 → 답변 내용 없음 표시');
      setTranscript('답변 내용 없음');
      setIsAnswerFinished(true); // 녹음 안 했어도 시간 초과면 답변 완료 상태로 전환
      isAnswerFinishedRef.current = true;
      setIsTranscriptLocked(true); // 녹음이 없었으므로 즉시 확정
      isTranscriptLockedRef.current = true;
      // [Fix] 절대 자동으로 nextQuestion()을 호출하지 않음. 사용자가 직접 버튼을 눌러야 함.
    }
  };

  useEffect(() => {
    if (step === 'interview' && interview && !pcRef.current) {
      const initMedia = async () => {
        // videoRef가 아직 DOM에 마운트되지 않았을 경우 한 틱 대기
        if (!videoRef.current) {
          console.warn('[Media Init] videoRef not ready, waiting 100ms...');
          await new Promise(r => setTimeout(r, 100));
        }
        try {
          await setupWebRTC(interview.id);
          setupWebSocket(interview.id);
          setupAiStreamWebSocket(interview.id); // [NEW] AI 스트리밍 연결
        } catch (err) {
          console.error("Media init error:", err);
        }
      };
      // React 렌더링 완료 후 실행 보장
      setTimeout(() => initMedia(), 0);
    }

    // 면접 진행 중 페이지 이탈 방지 경고
    const handleBeforeUnload = (e) => {
      if (step === 'interview') {
        const message = "면접 진행 중입니다. 페이지를 벗어나시면 현재까지의 답변이 정상적으로 분석되지 않을 수 있습니다. 면접을 종료하시려면 '면접 종료' 버튼을 눌러주세요.";
        e.returnValue = message;
        return message;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [step, interview]);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (aiStreamWsRef.current) aiStreamWsRef.current.close(); // [NEW]
      if (pcRef.current) pcRef.current.close();
      if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
    };
  }, []);

  return (
    <div className={['interview', 'profile', 'settings'].includes(step) ? `container ${step !== 'auth' ? 'has-header' : ''}` : 'full-screen-layout'}>
      {/* Header - Visible in Most Steps */}
      {step !== 'auth' && (
        <Header
          userName={parsedResumeData?.structured_data?.header?.name || parsedResumeData?.name || 'OOO'}
          onLogout={handleLogout}
          showLogout={!!user}
          onLogoClick={() => {
            if (step === 'interview') {
              alert("면접 진행 중에는 메인 화면으로 이동할 수 없습니다.\n면접을 종료하려면 '면접 종료' 버튼을 눌러주세요.");
              return;
            }
            if (user && (user.role === 'recruiter' || user.role === 'admin')) {
              setRecruiterMenu('dashboard');
              navigateSafe('recruiter_main');
            } else {
              navigateSafe('main');
            }
          }}
          isInterviewing={step === 'interview'}
          isComplete={step === 'complete'}
          isRecruiter={step === 'recruiter_main'}
          hideMenuButtons={step === 'recruiter_main'}
          onHistory={() => navigateSafe('history')}
          onAccountSettings={() => navigateSafe('settings')}
          onProfileManagement={() => navigateSafe('profile')}
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

      {/* 프로필 이탈 확인 모달 (헤더 네비게이션 가로채기) */}
      {showProfileLeaveModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 2000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)'
        }}>
          <div style={{
            background: 'var(--glass-bg, rgba(20,20,40,0.92))',
            border: '1px solid var(--glass-border)',
            borderRadius: '16px',
            padding: '2.5rem 2rem',
            maxWidth: '420px',
            width: '90%',
            boxShadow: '0 8px 40px rgba(0,0,0,0.4)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>💾</div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginBottom: '0.6rem', color: 'var(--text-main)' }}>
              저장하지 않은 변경 사항
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '2rem', lineHeight: '1.6' }}>
              프로필에 변경된 내용이 있습니다.<br />저장하고 이동하시겠습니까?
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <button
                onClick={() => {
                  setShowProfileLeaveModal(false);
                  setProfileDirty(false);
                  if (pendingStep) { setStep(pendingStep); setPendingStep(null); }
                }}
                style={{
                  padding: '10px 24px', borderRadius: '8px', border: '1px solid var(--glass-border)',
                  background: 'transparent', color: 'var(--text-main)', cursor: 'pointer', fontWeight: '600'
                }}
              >
                그냥 이동
              </button>
              <button
                onClick={async () => {
                  setShowProfileLeaveModal(false);
                  if (profileSaveRef.current) {
                    const ok = await profileSaveRef.current();
                    if (ok && pendingStep) { setStep(pendingStep); setPendingStep(null); }
                  }
                }}
                style={{
                  padding: '10px 24px', borderRadius: '8px', border: 'none',
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff', cursor: 'pointer', fontWeight: '600',
                  boxShadow: '0 2px 12px rgba(99,102,241,0.4)'
                }}
              >
                저장 후 이동
              </button>
            </div>
          </div>
        </div>
      )}



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
            totalQuestions={15} // 시나리오 기준 15단계 고정
            question={questions[currentIdx]?.content}
            audioUrl={questions[currentIdx]?.audio_url}
            isRecording={isRecording}
            isMediaReady={isMediaReady}
            transcript={transcript}
            setTranscript={setTranscript}
            toggleRecording={toggleRecording}
            nextQuestion={nextQuestion}
            onFinish={finishInterview}
            videoRef={videoRef}
            isLoading={isLoading}
            visionData={visionData}
            streamingQuestion={questions[currentIdx + 1]?.isStreaming ? questions[currentIdx + 1]?.content : null}
            onTimerEnd={handleTimerEnd}
            isAnswerFinished={isAnswerFinished}
            isTranscriptLocked={isTranscriptLocked}
            isSttProcessing={isSttProcessing} // [신규] 전달
          />
        )}

        {step === 'final_guide' && <FinalGuidePage onNext={initInterviewSession} onPrev={() => { setEnvTestStep('video'); setStep('env_test'); }} isLoading={isLoading} />}

        {step === 'complete' && (
          <InterviewCompletePage
            isReportLoading={isReportLoading}
            onCheckResult={() => {
              // [버그2 수정] 리포트가 아직 null이어도 result 페이지로 이동 허용
              // ResultPage 자체에서 report=null 시 "분석 중" 메시지를 보여줌
              sessionStorage.removeItem('from_history');
              setStep('result');
              console.log('[onCheckResult] report 상태:', report ? `id=${report.id}` : 'null (분석 중)');
            }}
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
              // reset flag
              sessionStorage.removeItem('from_history');
            }}
            onBack={
              // history에서 왔을 때만 함수를 전달 -> ResultPage에서 버튼 표시 여부 결정
              sessionStorage.getItem('from_history') === 'true'
                ? () => setStep('history')
                : null
            }
          />
        )}

        {step === 'history' && (
          <InterviewHistoryPage
            onBack={() => setStep('main')}
            onViewResult={(reportData, interviewData) => {
              setReport(reportData);
              setSelectedInterview(interviewData);
              // flag 설정: 이력 페이지에서 왔다
              sessionStorage.setItem('from_history', 'true');
              setStep('result');
            }}
          />
        )}

        {step === 'settings' && (
          <AccountSettingsPage
            onBack={() => setStep('main')}
            onLogout={handleLogout}
          />
        )}

        {step === 'profile' && (
          <ProfileManagementPage
            onBack={(force = false) => navigateSafe('main', force)}
            user={user}
            onSave={(updatedUser) => {
              setUser(updatedUser);
              setProfileDirty(false);
            }}
            onDirtyChange={(dirty) => setProfileDirty(dirty)}
            saveTriggerRef={profileSaveRef}
          />
        )}

        {step === 'recruiter_main' && (
          <RecruiterMainPage
            user={user}
            onLogout={handleLogout}
            onNavigate={(page) => setStep(page)}
            activeMenu={recruiterMenu}
            setActiveMenu={setRecruiterMenu}
          />
        )}

      </div>

      {/* 사용자 전용 테마 토글 플로팅 버튼 (관리자 페이지 제외) */}
      {step !== 'recruiter_main' && (
        <div className="no-print" style={{ position: 'fixed', bottom: '2rem', right: '2rem', zIndex: 1000 }}>
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
              transition: 'all 0.3s ease',
              outline: 'none'
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            {isDarkMode ? '☀️' : '🌑'}
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
