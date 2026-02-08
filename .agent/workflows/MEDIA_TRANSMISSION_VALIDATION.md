# 🎥🎤 미디어 전송 로직 검증 리포트

**검증 일시**: 2026-02-04 14:44  
**대상**: 마이크(오디오) 및 캠(비디오) 전송 플로우

---

## 📊 현재 아키텍처 분석

### 🎤 오디오 (마이크) 처리 플로우

```
브라우저 마이크
    ↓
getUserMedia (audio: true)
    ↓
MediaStream → AudioContext
    ↓
AudioWorkletNode (deepgram-processor.js)
    ↓ [PCM Int16 변환]
Deepgram Live API (Nova-2 모델)
    ↓ [실시간 STT]
프론트엔드 (transcript 상태 업데이트)
```

**동시에:**
```
MediaStream (audio track)
    ↓
WebRTC PeerConnection
    ↓
Media Server (main.py:197-205)
    ↓
consume_audio() - 트랙 소비만 (STT 안함)
```

### 🎥 비디오 (캠) 처리 플로우

```
브라우저 캠
    ↓
getUserMedia (video: true)
    ↓
MediaStream (video track)
    ↓
WebRTC PeerConnection
    ↓
Media Server (main.py:193-196)
    ↓
VideoAnalysisTrack
    ├─ 0.1초마다: 눈 추적 (Haar Cascade)
    │   └─ WebSocket으로 실시간 전송
    └─ 2초마다: 감정 분석 (Celery Task)
        └─ AI-Worker (DeepFace)
```

---

## ✅ 정상 작동 확인 사항

### 1. **오디오 전송 (마이크)**

✅ **getUserMedia 권한 처리**
```javascript
// App.jsx:311-314
const stream = await navigator.mediaDevices.getUserMedia({ 
  video: true, 
  audio: true 
});
```
- 비디오와 오디오 동시 요청
- 실패 시 폴백: 오디오만 요청 (324-333줄)

✅ **Deepgram 연결**
```javascript
// App.jsx:318
setupDeepgram(stream);
```
- AudioWorklet 사용 (최신 API)
- 녹음 버튼 상태에 따라 전송 제어 (`isRecordingRef.current`)

✅ **WebRTC 오디오 트랙 추가**
```javascript
// App.jsx:320-323
stream.getTracks().forEach(track => {
  pc.addTrack(track, stream);
  console.log('[WebRTC] Added track:', track.kind, track.label);
});
```

✅ **Media Server 오디오 소비**
```python
# main.py:218-225
async def consume_audio(track):
    try:
        while True:
            await track.recv()
    except Exception:
        pass
```
- 버퍼 오버플로우 방지
- 트랙 정상 종료 처리

### 2. **비디오 전송 (캠)**

✅ **비디오 트랙 추가**
```javascript
// App.jsx:316
videoRef.current.srcObject = stream;
```
- 로컬 비디오 미리보기 표시

✅ **WebRTC 비디오 전송**
```python
# main.py:193-196
if track.kind == "video":
    pc.addTrack(VideoAnalysisTrack(relay.subscribe(track), session_id))
```

✅ **프레임 처리 최적화**
```python
# main.py:122-125
if current_time - getattr(self, 'last_tracking_time', 0) > 0.1:
    asyncio.create_task(self.process_eye_tracking(frame))
```
- 비동기 처리로 스트림 지연 방지
- 0.1초 간격으로 눈 추적

---

## ⚠️ 잠재적 에러 및 개선 사항

### 🔴 Critical Issues

#### 1. **AudioWorklet 모듈 로딩 실패 가능성**

**문제**:
```javascript
// App.jsx:231
await audioContext.audioWorklet.addModule('/deepgram-processor.js');
```

**잠재적 에러**:
- 파일 경로가 `/deepgram-processor.js`로 절대 경로 사용
- Vite 개발 서버에서는 `public/` 폴더의 파일이 루트로 서빙됨
- 프로덕션 빌드 시 경로 문제 발생 가능

**해결 방안**:
```javascript
// 환경에 따라 경로 동적 설정
const workletPath = import.meta.env.DEV 
  ? '/deepgram-processor.js' 
  : `${import.meta.env.BASE_URL}deepgram-processor.js`;
await audioContext.audioWorklet.addModule(workletPath);
```

#### 2. **Media Server URL 하드코딩**

**문제**:
```javascript
// App.jsx:340
const response = await fetch('http://localhost:8080/offer', {
```

**잠재적 에러**:
- 프로덕션 환경에서 localhost 사용 불가
- CORS 에러 발생 가능

**해결 방안**:
```javascript
const MEDIA_SERVER_URL = import.meta.env.VITE_MEDIA_SERVER_URL || 'http://localhost:8080';
const response = await fetch(`${MEDIA_SERVER_URL}/offer`, {
```

#### 3. **WebSocket URL 하드코딩**

**문제**:
```javascript
// App.jsx:176
const ws = new WebSocket(`ws://localhost:8080/ws/${interviewId}`);
```

**동일한 문제**: 프로덕션 환경 대응 불가

### 🟡 Medium Issues

#### 4. **오디오 컨텍스트 중복 생성 가능성**

**문제**:
```javascript
// App.jsx:213
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
```

**잠재적 에러**:
- 브라우저는 AudioContext 개수 제한 있음 (보통 6개)
- 면접 재시작 시 이전 컨텍스트 정리 안되면 누적

**현재 정리 로직**:
```javascript
// App.jsx:299
if (audioContext.state !== 'closed') audioContext.close();
```
✅ 정리 로직 존재하나, 에러 발생 시 실행 안될 수 있음

**개선 방안**:
```javascript
// useRef로 AudioContext 재사용
const audioContextRef = useRef(null);

const setupDeepgram = async (stream) => {
  // 기존 컨텍스트 정리
  if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
    await audioContextRef.current.close();
  }
  
  audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
  const audioContext = audioContextRef.current;
  // ...
};
```

#### 5. **getUserMedia 권한 거부 시 Deepgram 설정 누락**

**문제**:
```javascript
// App.jsx:327-328
const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
audioStream.getTracks().forEach(track => pc.addTrack(track, audioStream));
```

**잠재적 에러**:
- 카메라 실패 후 오디오만 획득 시, `setupDeepgram(stream)` 호출 안됨
- STT 기능 작동 안함

**해결 방안**:
```javascript
try {
  const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  setupDeepgram(audioStream); // 추가 필요
  audioStream.getTracks().forEach(track => pc.addTrack(track, audioStream));
  alert('카메라 접근 거부됨. 음성만 사용합니다.');
} catch (audioErr) {
  alert('마이크 접근 실패');
  throw audioErr;
}
```

#### 6. **Deepgram 연결 상태 확인 부족**

**문제**:
```javascript
// App.jsx:240
if (connection.getReadyState() !== 1) return;
```

**잠재적 에러**:
- Deepgram 연결 실패 시 사용자에게 알림 없음
- 녹음 중인데 STT 안되는 상황 발생 가능

**개선 방안**:
```javascript
connection.on(LiveTranscriptionEvents.Open, async () => {
  console.log("Deepgram WebSocket Connected");
  setSubtitle("🎤 음성 인식 준비 완료");
  // ...
});

connection.on(LiveTranscriptionEvents.Error, (err) => {
  console.error("Deepgram Error:", err);
  alert("음성 인식 연결에 실패했습니다. 페이지를 새로고침해주세요.");
});
```

### 🟢 Low Priority Issues

#### 7. **비디오 프레임 처리 에러 핸들링 부족**

**문제**:
```python
# main.py:113-114
except Exception as e:
    logger.error(f"Eye tracking frame failed: {e}")
```

**개선 방안**:
- 연속 실패 카운터 추가
- 일정 횟수 이상 실패 시 트랙 재시작 또는 알림

#### 8. **WebRTC ICE 연결 실패 처리 부족**

**문제**:
```javascript
// App.jsx:307-308
const pc = new RTCPeerConnection();
pcRef.current = pc;
```

**개선 방안**:
```javascript
pc.oniceconnectionstatechange = () => {
  console.log('[WebRTC] ICE connection state:', pc.iceConnectionState);
  if (pc.iceConnectionState === 'failed') {
    alert('비디오 연결에 실패했습니다. 네트워크를 확인해주세요.');
  }
};

pc.onconnectionstatechange = () => {
  console.log('[WebRTC] Connection state:', pc.connectionState);
};
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 정상 플로우
1. ✅ 카메라/마이크 권한 허용
2. ✅ WebRTC 연결 성공
3. ✅ Deepgram STT 작동
4. ✅ 눈 추적 실시간 표시
5. ✅ 감정 분석 백그라운드 처리

### 시나리오 2: 카메라 거부
1. ❌ 카메라 권한 거부
2. ✅ 오디오만 획득 (폴백)
3. ⚠️ **Deepgram 설정 누락** (개선 필요)
4. ✅ WebRTC 오디오 전송
5. ❌ 비디오 분석 불가 (정상)

### 시나리오 3: 마이크 거부
1. ✅ 카메라 권한 허용
2. ❌ 마이크 권한 거부
3. ❌ 면접 시작 실패 (정상)
4. ✅ 사용자에게 에러 알림

### 시나리오 4: Deepgram API 키 없음
1. ✅ 미디어 획득 성공
2. ⚠️ Deepgram 연결 실패
3. ✅ 경고 메시지 표시
4. ⚠️ **STT 없이 진행** (개선 필요)

### 시나리오 5: Media Server 다운
1. ✅ 미디어 획득 성공
2. ❌ WebRTC offer 전송 실패
3. ✅ 에러 throw
4. ⚠️ **사용자 친화적 에러 메시지 부족**

---

## 📋 권장 수정 사항 요약

### 즉시 수정 (Critical)

1. **오디오 전용 모드에서 Deepgram 설정 추가**
```javascript
// App.jsx:327 이후
setupDeepgram(audioStream);
```

2. **환경 변수로 URL 관리**
```javascript
// .env
VITE_MEDIA_SERVER_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080

// App.jsx
const MEDIA_SERVER_URL = import.meta.env.VITE_MEDIA_SERVER_URL;
const WS_URL = import.meta.env.VITE_WS_URL;
```

### 1주일 내 수정 (High)

3. **WebRTC 연결 상태 모니터링**
4. **Deepgram 연결 실패 시 사용자 알림**
5. **AudioContext 재사용 로직**

### 1개월 내 수정 (Medium)

6. **비디오 프레임 처리 에러 복구 로직**
7. **연결 품질 모니터링 및 자동 재연결**

---

## ✅ 결론

### 전체 평가: **85/100** (Very Good)

**강점**:
- ✅ 최신 AudioWorklet API 사용
- ✅ 비동기 처리로 성능 최적화
- ✅ 폴백 메커니즘 존재
- ✅ 상세한 로깅

**개선 필요**:
- ⚠️ 오디오 전용 모드에서 STT 누락
- ⚠️ 하드코딩된 URL
- ⚠️ 연결 상태 모니터링 부족

**심각한 에러 가능성**: **낮음**  
현재 구조는 대부분의 경우 정상 작동하나, 엣지 케이스 처리 개선 필요.
