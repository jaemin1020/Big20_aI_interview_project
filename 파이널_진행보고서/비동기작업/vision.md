# Vision Task 모듈 (vision.py)

면접자의 영상 데이터를 분석하여 감정 및 시선을 추적하는 비동기 작업을 수행합니다.

## 주요 기능

### 1. `tasks.vision.analyze_emotion`
- **설명**: 지원자의 프레임(Base64 이미지)을 분석하여 현재 감정 상태를 파악합니다.
- **사용 기술**: `DeepFace`
- **매개변수**:
    - `session_id`: 인터뷰 세션 ID
    - `base64_img`: 분석할 이미지 데이터 (Base64)
- **결과**: `dominant_emotion`(주요 감정), `score` 등을 반환하며 DB에 감정 정보를 업데이트합니다.

### 2. `tasks.vision.track_eyes`
- **설명**: 지원자의 시선이 화면을 향하고 있는지(집중도)를 추적합니다.
- **사용 기술**: `OpenCV (Haar Cascade)`
- **매개변수**:
    - `session_id`: 인터뷰 세션 ID
    - `base64_img`: 분석할 이미지 데이터 (Base64)
- **결과**: 얼굴 영역 및 눈 위치 정보를 포함하며, `focused` 등의 상태값을 DB에 저장합니다. 디버깅용 시각화 이미지도 포함됩니다.
