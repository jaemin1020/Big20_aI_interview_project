# 🎯 AI 모의면접 시스템 - 전체 파이프라인 현황

**최종 업데이트**: 2026년 2월 6일 15:16  
**문서 목적**: 전체 면접 흐름의 각 단계별 구현 상태 및 작업 이력 추적  
**규칙**: ⚠️ 이 문서는 **업데이트 전용**입니다. 기존 작업 이력을 삭제하지 않습니다.

---

## 📊 전체 파이프라인 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│  [1] 면접 사이트 접속                                                │
│       └─▶ frontend/ (React)                                        │
├─────────────────────────────────────────────────────────────────────┤
│  [2] 회원가입 및 로그인                                              │
│       └─▶ backend-core/routes/auth.py                              │
├─────────────────────────────────────────────────────────────────────┤
│  [3] 이력서 제출                                                     │
│       └─▶ backend-core/routes/resumes.py → ai-worker/resume_parser │
├─────────────────────────────────────────────────────────────────────┤
│  [4] 면접 생성 & 질문 생성 (LLM)                                     │
│       └─▶ ai-worker/tasks/question_generator.py (EXAONE)           │
├─────────────────────────────────────────────────────────────────────┤
│  [5] AI 면접관 소환 & WebRTC 연결                                    │
│       └─▶ media-server/main.py                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [6] 영상 분석 (Vision) - 실시간                                     │
│       └─▶ ai-worker/tasks/vision.py (DeepFace + OpenCV)            │
├─────────────────────────────────────────────────────────────────────┤
│  [7] AI 면접관이 질문 (TTS)                                          │
│       └─▶ ai-worker/stt_poc/tts_test_qwen.py (Qwen3-TTS)           │
├─────────────────────────────────────────────────────────────────────┤
│  [8] 면접자 답변 → 텍스트 변환 (STT)                                 │
│       └─▶ media-server/main.py (Whisper Large-v3)                  │
├─────────────────────────────────────────────────────────────────────┤
│  [9] 답변 평가 & 꼬리질문 (LLM)                                      │
│       └─▶ ai-worker/tasks/evaluator.py (EXAONE)                    │
├─────────────────────────────────────────────────────────────────────┤
│  [10] 면접 종료 & 결과 리포트                                        │
│       └─▶ ai-worker/tasks/evaluator.py → backend-core DB           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 단계별 구현 상태

| # | 단계 | 담당 모듈 | 상태 | 비고 |
|---|------|----------|------|------|
| 1 | 면접 사이트 접속 | `frontend/` | ✅ 완료 | React 기반 |
| 2 | 회원가입/로그인 | `backend-core/routes/auth.py` | ✅ 완료 | JWT 인증 |
| 3 | 이력서 제출 | `resume_parser.py` | ✅ 완료 | PDF 파싱 + 임베딩 |
| 4 | 질문 생성 (LLM) | `question_generator.py` | ✅ 완료 | EXAONE-3.5-7.8B |
| 5 | WebRTC 연결 | `media-server/main.py` | ✅ 완료 | aiortc 기반 |
| 6 | 영상 분석 (Vision) | `vision.py` | ✅ 완료 | DeepFace + OpenCV |
| 7 | 질문 음성화 (TTS) | `tts_test_qwen.py` | ✅ PoC 완료 | Qwen3-TTS |
| 8 | 음성→텍스트 (STT) | `media-server/main.py` | ✅ 완료 | Whisper Large-v3 |
| 9 | 답변 평가 (LLM) | `evaluator.py` | ✅ 완료 | EXAONE |
| 10 | 결과 리포트 | `evaluator.py` | ✅ 완료 | DB 저장 |

---

## 🔗 모듈 간 연결 상태

| 연결 | 상태 | 설명 |
|------|------|------|
| STT → Evaluator | ⚠️ 미연결 | STT 결과가 DB에만 저장되고 평가기 호출 안 됨 |
| Evaluator → Question Generator | ⚠️ 미연결 | 꼬리질문 생성 로직 미구현 |
| Question Generator → TTS | ⚠️ 미연결 | 질문 텍스트 → 음성 변환 연결 안 됨 |
| TTS → Frontend | ⚠️ 미연결 | 음성 파일 전송 로직 없음 |
| Vision → WebSocket | ✅ 연결됨 | 실시간 감정/시선 데이터 전송 |

---

## 📝 작업 이력 로그 (누적 기록)

> ⚠️ **규칙**: 새 작업은 맨 아래에 추가합니다. 기존 기록을 수정하거나 삭제하지 않습니다.

### [2026-02-05] Vision 모델 개발
- **작업자**: CYJ
- **작업 내용**: 
  - MediaPipe 기반 얼굴 랜드마크 추출 구현
  - 실시간 시선/자세 추적 로직 개발
  - 감정 인식 민감도 튜닝 (슬픔/놀람)
  - 하이브리드 아키텍처 도입 (DeepFace + MediaPipe)
- **결과**: `CV-V2-TASK.py` 완성

### [2026-02-06 오전] TTS 모듈 통합 테스트
- **작업자**: CYJ + AI
- **작업 내용**:
  - `qwen-tts` 라이브러리 설치 (`pip install qwen-tts`)
  - `CYJ/tts_service.py` 독립 모듈 생성
  - `CYJ/main_test.py` 통합 테스트 스크립트 작성
  - Mock 모드 구현 (라이브러리 없을 때 비프음 생성)
  - `import torch` 누락 오류 수정
- **결과**: TTS 음성 파일 생성 성공 (`test_interview_XXXXX.wav`)

### [2026-02-06 오후] 전체 프로젝트 스캔 및 통합 계획
- **작업자**: AI
- **작업 내용**:
  - 전체 프로젝트 구조 스캔 (.env 제외)
  - LLM, STT, TTS, Vision 구현 상태 확인
  - 모듈 간 연결 누락 지점 분석
  - 전체 파이프라인 문서 작성 (본 문서)
- **결과**: 모든 핵심 모듈 구현 완료 확인, 연결 작업 필요

### [2026-02-06 16:08] TTS 모델 비교 구현
- **작업자**: CYJ + AI
- **작업 내용**:
  - `tts_test_qwen.py` → `tts_qwen3.py`로 이름 변경 (명확성)
  - `tts_styletts2.py` 신규 생성 (5Hyeons/StyleTTS2 한국어 모델)
  - `TTSBase` 추상 클래스 정의 (통합용 공통 인터페이스)
  - `tts_compare.py` 비교 테스트 스크립트 생성
  - 모든 코드에 상세 주석 추가 (단계별 설명)
- **결과**: 
  - Qwen3-TTS: 즉시 사용 가능 (pip install qwen-tts)
  - StyleTTS2: GitHub clone + 모델 다운로드 필요
- **다음 단계**: StyleTTS2 설치 후 비교 테스트 실행

### [2026-02-06 16:18] StyleTTS2 설치 완료
- **작업자**: CYJ + AI
- **작업 내용**:
  - GitHub 클론: `/app/libs/StyleTTS2-Vocos` (57개 파일)
  - Hugging Face 다운로드: `/app/models/styletts2` (21개 파일, ~4.3GB)
    - `Vocos/AIHUB_ML/epoch_1st_00014.pth` (~2.1GB)
    - `Vocos/AIHUB_ML/epoch_2nd_00006.pth` (~2.3GB)
    - `Vocos/AIHUB_ML/config_aihub_multi_lingual_en_jp_ko_zh_vocos.yml`
    - `Vocos/LibriTTS/` (영어 모델)
  - 의존성 설치: pyyaml, vocos, phonemizer
- **결과**: ✅ 설치 성공 (토큰 불필요, 공개 모델)
- **다음 단계**: TTS 비교 테스트 실행

---

## 🎯 다음 작업 (To-Do)

- [ ] STT 결과 → Celery로 `evaluator.analyze_answer` 자동 호출
- [ ] 질문 생성 완료 → TTS 음성 생성 연결
- [ ] TTS 음성 → WebSocket으로 Frontend 전송
- [ ] 전체 루프 통합 테스트

---

## 📁 관련 문서 링크

- [에러 노트 (AI_DEV_LOG.md)](file:///c:/big20/Big20_aI_interview_project/ai-worker/cv_poc/AI_DEV_LOG.md)
