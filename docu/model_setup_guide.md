# AI 모델 다운로드 및 설정 가이드

본 프로젝트에서 사용하는 대형 언어 모델(LLM)과 관련 파일들을 다운로드하고 설정하는 방법입니다.

## 1. Solar-10.7B (정밀 평가용)

**사용 목적**: 답변의 기술적 정확성, 논리성 등을 정밀하게 평가 (CPU 구동)  
**파일 위치**: `c:\big20\Big20_aI_interview_project\ai-worker\models\`  
**파일명**: `solar-10.7b-instruct-v1.0.Q8_0.gguf` (약 11GB)

### 방법 A: 자동 다운로드 스크립트 실행 (추천)
가장 간편한 방법입니다.

1. 터미널(PowerShell)을 엽니다.
2. `ai-worker` 폴더로 이동합니다.
   ```powershell
   cd c:\big20\Big20_aI_interview_project\ai-worker
   ```
3. 다운로드 스크립트를 실행합니다.
   ```powershell
   python.exe download_solar_model.py
   ```
   *(스크립트가 없다면, `README.md`나 에이전트에게 요청하여 생성하세요)*

### 방법 B: 수동 다운로드
인터넷 브라우저나 다른 도구를 사용해 직접 다운로드합니다.

1. **다운로드 링크 접속**: [TheBloke/Solar-10.7B-Instruct-v1.0-GGUF](https://huggingface.co/TheBloke/Solar-10.7B-Instruct-v1.0-GGUF/tree/main)
2. 파일 목록에서 `solar-10.7b-instruct-v1.0.Q8_0.gguf`를 찾습니다.
3. 다운로드 버튼(↓)을 클릭하여 저장합니다.
4. 다운로드된 파일을 아래 경로로 이동시킵니다.
   - `c:\big20\Big20_aI_interview_project\ai-worker\models\solar-10.7b-instruct-v1.0.Q8_0.gguf`

---

## 2. DeepFace (감정 분석용)

**사용 목적**: 사용자 웹캠 영상의 표정 감정 분석  
**다운로드**: 자동

DeepFace 모델(`vgg_face_weights.h5` 등)은 `ai-worker`가 처음 실행될 때 (`tasks.vision` 모듈이 로드될 때) 자동으로 `~/.deepface/weights/` 경로에 다운로드됩니다. 별도의 수동 다운로드가 필요 없습니다.

---

## 3. Llama-3.1-8B (실시간 질문 생성용)

**사용 목적**: 직무별 맞춤 면접 질문 생성 (GPU 구동)  
**다운로드**: 자동 (HuggingFace Hub)

`backend-core` 컨테이너가 실행될 때, `HUGGINGFACE_HUB_TOKEN`을 사용하여 자동으로 캐시 디렉토리에 다운로드합니다.
단, `.env` 파일에 유효한 토큰이 반드시 있어야 합니다.

```ini
# .env 파일 예시
HUGGINGFACE_HUB_TOKEN=hf_your_token_here
```
