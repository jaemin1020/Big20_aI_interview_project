# 📹 Media Server & Vision Analysis

실시간 화상 면접의 핵심인 **WebRTC 스트리밍**과 **MediaPipe 기반의 비언어적 행동 분석** 시스템을 설명합니다.

---

## 1. WebRTC 기반 스트리밍 (aiortc)

본 프로젝트는 브라우저와 서버 간의 저지연(Low Latency) 미디어 전송을 위해 **aiortc** 라이브러리를 사용합니다.

- **Signaling**: HTTP POST (`/offer`)를 통해 SDP 정보를 교환하며 연결 수립.
- **NAT Traversal**: 도커 환경에서의 안정적인 연결을 위해 고정된 포트 범위(UDP 10000-10100)를 사용하도록 몽키 패치(Monkey Patch) 적용.
- **Track Management**: 
  - `VideoAnalysisTrack`: 수신된 비디오 프레임을 캡처하여 분석 루틴에 전달.
  - `STT 처리`: 오디오 트랙을 WAV 조각으로 인코딩하여 AI-Worker의 Faster-Whisper 작업으로 비동기 위임.

---

## 2. 비전 분석 엔진 (MediaPipe)

MediaPipe의 **FaceLandmarker**를 사용하여 지원자의 비언어적 태도를 실시간(약 5FPS)으로 수집합니다.

### 📊 분석 지표
- **시선 (Gaze)**: 눈동자의 랜드마크 변화를 감지하여 면접관(카메라)을 응시하는지 여부 판별.
- **자세 (Posture)**: 머리의 회전 각도(Pitch, Yaw, Roll)를 계산하여 바른 자세 유지 여부 확인.
- **표정 (Emotion/Smile)**: 입꼬리의 좌표 변화를 측정하여 미소 및 긴장도 분석.
- **데이터 흐름**: 분석된 데이터는 실시간으로 WebSocket을 통해 프론트엔드 UI에 전달되어 대시보드에 반영됩니다.

---

## 3. 오디오 자신감 분석 (RMS)

음성 데이터의 파형 에너지를 수치화하여 지원자의 발화 자신감을 분석합니다.

- **볼륨 (dB)**: RMS(Root Mean Square) 계산을 통해 평균 음압을 측정.
- **발화율 (Speaking Ratio)**: 전체 녹음 시간 대비 실제 음성이 검출된 비율 계산.
- **피드백**: 실시간으로 "안정적입니다", "조금 더 크게 말씀해 보세요" 등의 메시지를 WebSocket으로 실시간 전송.

---

## 4. 실시간 긴장도 모니터링

수집된 비전/오디오 지표들을 가중합하여 **최종 긴장도(Anxiety Score)**를 산출합니다.

- **저장**: Redis에 실시간으로 점수를 기록하여 면접 진행 중 실시간 모니터링 가능.
- **최종 반영**: 면접이 종료되면 해당 점수들을 평균화하여 `interviews` 테이블의 `emotion_summary` 컬럼에 JSON 형태로 영구 저장.

---
*문서 위치: `docs/readmelist/SIGNALING_MEDIA_SERVER.md`*
