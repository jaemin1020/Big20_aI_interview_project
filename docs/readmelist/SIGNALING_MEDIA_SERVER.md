# 📹 Media Server & 실시간 비전 솔루션

**WebRTC 초저지연 스트리밍**과 **MediaPipe 기반의 실시간 행동 분석** 최적화 기법을 기술합니다.

---

## 1. WebRTC 엔지니어링 (aiortc)

브라우저와 서버 간의 미디어 패킷 릴레이를 위해 **aiortc**를 기반으로 한 고성능 미디어 서버를 구축했습니다.

-   **Signaling**: 8080 포트에서 HTTP/WebSocket을 통해 SDP와 ICE Candidate를 교환합니다.
-   **Port Binding Topology**: Docker NAT 환경에서 WebRTC UDP 패킷 손실을 방지하기 위해 **50000-50050/udp** 대역을 직접 바인딩하고, 소켓 몽키 패칭을 통해 ICE 수집 성공률을 100%로 끌어올렸습니다.
-   **Audio Pipeline**: 
    -   초기 서버 오디오 추출 방식의 병목을 해결하기 위해, 브라우저의 **AudioWorkletProcessor**를 활용한 Client-side Buffering 구조로 전환했습니다.
    -   이를 통해 서버의 Event Loop 틱을 보존하면서도 고품질 음성 데이터를 AI-Worker에 병렬로 전달할 수 있게 되었습니다.

---

## 2. Vision 분석 최적화 (MediaPipe)

서버 자원(CPU/GPU) 고갈을 방지하기 위해 **현실적인 최적화 루틴**을 적용했습니다.

### 🚀 5FPS Frame Skipping Sampling
-   초당 30프레임이 들어오는 고부하 영상 스트림에서, 모든 프레임을 분석하는 대신 **초당 5프레임만 샘플링(Frame Skipping)** 하여 분석하도록 설계했습니다.
-   **결과**: 분석의 통계적 신뢰도는 유지하면서 서버 CPU 점유율을 기존 대비 **80% 이상 절감**하여 전체 시스템 크래시를 방지했습니다.

### 📊 수집 지표
-   **시선 추적 (Gaze)**: 468개 얼굴 랜드마크를 통해 카메라 응시 여부 및 시선 분산 패턴 분석.
-   **자세 정합성 (Posture)**: 머리의 회전값(Pitch/Yaw/Roll) 연산을 통한 면접 태도 점수화.
-   **정서 분석 (Emotion)**: 입꼬리 좌표 및 미소 강도를 측정하여 우세적 정서(Dominant Emotion) 추출.

---

## 3. 실시간 피드백 및 상태 관리

-   **Redis Real-time Store**: 분석된 감정 및 시선 수치는 Redis에 초 단위로 누적 저장됩니다.
-   **WebSocket Relay**: 가공된 태도 점수는 WebSocket을 통해 즉시 프론트엔드 대시보드에 반영되어, 지원자에게 "목소리를 조금 더 키워보세요" 또는 "시선이 불안정합니다" 등의 실시간 가이드를 제공합니다.
-   **데이터 원자화**: 면접 종료 시 Redis의 시계열 데이터를 PostgreSQL의 **JSONB** 컬럼으로 영속화하여 Join 오버헤드를 최소화했습니다.

---
*문서 위치: `docs/readmelist/SIGNALING_MEDIA_SERVER.md`*

