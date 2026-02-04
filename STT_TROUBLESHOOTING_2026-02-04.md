# 🎤 음성인식 작동 안 되는 문제 분석 리포트

**분석 일시**: 2026-02-04 14:57  
**분석 대상**: Deepgram STT 통합

---

## 🔍 발견된 문제점

### 1️⃣ **환경 변수 미설정** 🔴 Critical

**문제**:
- `.env` 파일이 프로젝트에 존재하지 않음
- `DEEPGRAM_API_KEY`가 설정되지 않아 백엔드에서 토큰 발급 불가

**증상**:
```javascript
// 프론트엔드 콘솔 에러
Failed to get Deepgram token from backend
// 또는
Deepgram API key not configured on server
```

**해결 방법**:
```bash
# backend-core/.env 파일 생성
DEEPGRAM_API_KEY=your_deepgram_api_key_here
DATABASE_URL=postgresql://user:password@postgres:5432/ai_interview
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
SECRET_KEY=your_jwt_secret_key_here
```

---

### 2️⃣ **AudioWorklet 파일 로딩 실패** 🔴 Critical

**문제**:
```javascript
// App.jsx:251
await audioContext.audioWorklet.addModule('/deepgram-processor.js');
```

Vite 개발 서버에서 `/deepgram-processor.js` 경로가 올바르게 해석되지 않을 수 있음

**증상**:
```
AudioWorklet setup failed: Failed to fetch
```

**해결 방법**:

**옵션 1**: Public 폴더 사용 (현재 구조)
```javascript
// vite.config.js에서 public 디렉토리 확인
export default defineConfig({
  publicDir: 'public',  // 이 설정 확인
  // ...
})
```

**옵션 2**: 절대 경로 사용
```javascript
await audioContext.audioWorklet.addModule(
  new URL('/deepgram-processor.js', import.meta.url).href
);
```

**옵션 3**: Inline AudioWorklet (권장)
```javascript
// AudioWorklet 코드를 Blob으로 인라인화
const processorCode = `
class DeepgramProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input && input.length > 0) {
      const channelData = input[0];
      const buffer = new Int16Array(channelData.length);
      for (let i = 0; i < channelData.length; i++) {
        const s = Math.max(-1, Math.min(1, channelData[i]));
        buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      this.port.postMessage(buffer.buffer, [buffer.buffer]);
    }
    return true;
  }
}
registerProcessor('deepgram-processor', DeepgramProcessor);
`;

const blob = new Blob([processorCode], { type: 'application/javascript' });
const processorUrl = URL.createObjectURL(blob);
await audioContext.audioWorklet.addModule(processorUrl);
```

---

### 3️⃣ **Sample Rate 불일치** 🟡 Medium

**문제**:
```javascript
// 프론트엔드: 브라우저의 기본 sample rate (보통 48000Hz)
const sampleRate = audioContext.sampleRate;

// 백엔드: 고정값 16000Hz
sample_rate=16000
```

**영향**: 음성 인식 정확도 저하, 음성 속도 왜곡

**해결 방법**:

**옵션 1**: 프론트엔드에서 리샘플링
```javascript
// AudioContext를 16000Hz로 생성 (일부 브라우저에서 지원 안 됨)
const audioContext = new AudioContext({ sampleRate: 16000 });
```

**옵션 2**: 백엔드에서 동적으로 설정
```javascript
// 프론트엔드에서 sample rate 전송
const connection = deepgram.listen.live({
  model: "nova-2",
  language: "ko",
  smart_format: true,
  encoding: "linear16",
  sample_rate: sampleRate,  // 브라우저의 실제 sample rate 사용
});
```

---

### 4️⃣ **녹음 상태 관리 문제** 🟡 Medium

**문제**:
```javascript
// App.jsx:259 - 녹음 중이 아니면 오디오 전송 안 함
if (!isRecordingRef.current) return;
```

**증상**: 
- 사용자가 "녹음 시작" 버튼을 누르지 않으면 음성 인식 안 됨
- 자막이 표시되지 않음

**확인 방법**:
1. 면접 화면에서 "🎤 녹음 시작" 버튼 클릭 확인
2. 버튼이 "⏸ 녹음 중지"로 변경되는지 확인

**개선 방안**:
```javascript
// 자동 녹음 시작 옵션 추가
useEffect(() => {
  if (step === 'interview' && questions.length > 0) {
    // 첫 질문이 표시되면 자동으로 녹음 시작
    setIsRecording(true);
    isRecordingRef.current = true;
  }
}, [step, questions]);
```

---

### 5️⃣ **CORS 설정 확인** 🟢 Low

**확인 사항**:
```python
# backend-core/main.py:41
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
```

Vite 개발 서버는 기본적으로 `http://localhost:5173`을 사용하므로 CORS에 추가 필요

**해결**:
```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

### 6️⃣ **WebSocket 연결 문제** 🟡 Medium

**잠재적 문제**:
```javascript
// App.jsx:184
const ws = new WebSocket(`ws://localhost:8080/ws/${interviewId}`);
```

Media Server의 WebSocket과 STT WebSocket이 혼동될 수 있음

**확인**:
- Media Server WebSocket: `ws://localhost:8080/ws/{interview_id}`
- STT WebSocket (미사용): `ws://localhost:8000/stt/ws/{interview_id}`

현재 구조에서는 Deepgram SDK가 직접 Deepgram 서버와 WebSocket 연결을 맺으므로 백엔드 WebSocket 프록시는 **사용되지 않음**

---

## 🛠️ 즉시 적용 가능한 해결책

### Step 1: 환경 변수 설정
```bash
# backend-core/.env 생성
cat > backend-core/.env << EOF
DEEPGRAM_API_KEY=your_actual_deepgram_api_key
DATABASE_URL=postgresql://user:password@postgres:5432/ai_interview
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
SECRET_KEY=your_jwt_secret_key
EOF
```

### Step 2: AudioWorklet 인라인화 (App.jsx 수정)
```javascript
// setupDeepgram 함수 내부, audioContext.audioWorklet.addModule 호출 전에:
const processorCode = `
class DeepgramProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input && input.length > 0) {
      const channelData = input[0];
      const buffer = new Int16Array(channelData.length);
      for (let i = 0; i < channelData.length; i++) {
        const s = Math.max(-1, Math.min(1, channelData[i]));
        buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      this.port.postMessage(buffer.buffer, [buffer.buffer]);
    }
    return true;
  }
}
registerProcessor('deepgram-processor', DeepgramProcessor);
`;

const blob = new Blob([processorCode], { type: 'application/javascript' });
const processorUrl = URL.createObjectURL(blob);
await audioContext.audioWorklet.addModule(processorUrl);
URL.revokeObjectURL(processorUrl); // 메모리 정리
```

### Step 3: 디버깅 로그 추가
```javascript
// setupDeepgram 함수 시작 부분
console.log('🎤 [STT] Starting Deepgram setup...');
console.log('🎤 [STT] Stream tracks:', stream.getTracks().map(t => ({
  kind: t.kind,
  enabled: t.enabled,
  muted: t.muted
})));

// 토큰 받은 후
console.log('🎤 [STT] Token received, API key length:', api_key?.length);

// AudioWorklet 로드 후
console.log('🎤 [STT] AudioWorklet loaded successfully');

// Deepgram 연결 후
connection.on(LiveTranscriptionEvents.Open, async () => {
  console.log('🎤 [STT] Deepgram connection OPEN');
  // ...
});
```

### Step 4: 녹음 자동 시작
```javascript
// toggleRecording 함수 대신 자동 시작
useEffect(() => {
  if (step === 'interview' && questions.length > 0 && !isRecording) {
    console.log('🎤 Auto-starting recording...');
    setIsRecording(true);
    isRecordingRef.current = true;
  }
}, [step, questions]);
```

---

## 🧪 테스트 체크리스트

- [ ] 백엔드 `.env` 파일에 `DEEPGRAM_API_KEY` 설정됨
- [ ] 백엔드 서버 재시작 (`docker-compose restart backend-core`)
- [ ] 브라우저 콘솔에서 "✅ Deepgram token received from backend" 메시지 확인
- [ ] 브라우저 콘솔에서 "Deepgram WebSocket Connected" 메시지 확인
- [ ] 마이크 권한 허용 확인
- [ ] "🎤 녹음 시작" 버튼 클릭 또는 자동 시작 확인
- [ ] 말할 때 실시간 자막(subtitle) 표시 확인
- [ ] 최종 transcript에 텍스트 누적 확인

---

## 📊 예상 에러 메시지 및 해결

| 에러 메시지 | 원인 | 해결 |
|------------|------|------|
| `Failed to get Deepgram token from backend` | 백엔드 연결 실패 또는 인증 실패 | 백엔드 실행 확인, JWT 토큰 확인 |
| `Deepgram API key not configured on server` | 환경 변수 미설정 | `.env` 파일 생성 및 `DEEPGRAM_API_KEY` 설정 |
| `AudioWorklet setup failed` | AudioWorklet 파일 로딩 실패 | 인라인 Blob 방식으로 변경 |
| `401 Unauthorized` (Deepgram) | 잘못된 API 키 | Deepgram 대시보드에서 API 키 확인 |
| 자막이 안 나옴 | 녹음 상태가 false | "녹음 시작" 버튼 클릭 또는 자동 시작 |

---

**작성자**: Antigravity AI  
**다음 단계**: 위 해결책 적용 후 재테스트
