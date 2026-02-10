# 프론트엔드 기술 스택 분석

## 개요
이 프로젝트의 프론트엔드는 **React**와 **Vite**를 기반으로 구축되었습니다. `GlassCard`, `PremiumButton`과 같은 커스텀 컴포넌트 라이브러리와 CSS(`animate-fade-in`, 변수 활용)를 사용하여 스타일링되었습니다.

## 공통 의존성 (Dependencies)
*   **React**: 핵심 라이브러리 (Hooks: `useState`, `useEffect`, `useRef` 사용).
*   **Axios**: API 요청을 위한 HTTP 클라이언트 (API import 코드에서 확인됨).
*   **React Router**: 페이지 이동 및 라우팅 (페이지 구조에서 확인됨).
*   **Custom Components**: `GlassCard` (유리 형태 카드 UI), `PremiumButton` (버튼 UI).

---

## 페이지별 기술 분석

### 1. 메인 페이지 ([/src/pages/main/MainPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/main/MainPage.jsx))
*   **핵심 로직**: 사용자 로그인 상태에 따라 조건부 렌더링을 수행하는 랜딩 페이지입니다.
*   **주요 기능 및 기술**:
    *   **동적 드롭다운 메뉴**: 프로필, 이력 등의 메뉴를 CSS 애니메이션과 함께 제공합니다.
    *   **CSS-in-JS**: `<style>` 태그를 사용하여 특정 애니메이션(`fadeIn`)을 정의했습니다.
    *   **스타일링**: 백그라운드 블러(Backdrop Filter) 및 글래스모피즘(Glassmorphism) 효과를 적용했습니다.

### 2. 인증 페이지 ([/src/pages/auth/AuthPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/auth/AuthPage.jsx))
*   **핵심 로직**: 로그인 및 회원가입 폼을 처리합니다.
*   **주요 기능 및 기술**:
    *   **이미지 프리뷰**: `FileReader` API를 사용하여 프로필 이미지 업로드 전 미리보기를 제공합니다.
    *   **폼 유효성 검사**: 이메일 형식, 비밀번호 일치 여부, 필수 항목 체크 등 클라이언트 사이드 검증을 수행합니다.
    *   **상태 관리**: 로그인/회원가입 모드를 상태(`state`)로 관리하여 화면을 전환합니다.

### 3. 면접 이력 페이지 ([/src/pages/history/InterviewHistoryPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/history/InterviewHistoryPage.jsx))
*   **핵심 로직**: 과거 면접 기록을 목록으로 보여주고 필터링 기능을 제공합니다.
*   **주요 기능 및 기술**:
    *   **클라이언트 필터링**: 날짜(1개월, 3개월, 기간 설정), 회사명, 직무별로 데이터를 필터링합니다.
    *   **데이터 시각화**: 면접 상태(완료/진행 중)를 배지(Badge) 형태로 시각화했습니다.
    *   **API 통합**: 전체 면접 목록 및 특정 결과 리포트 데이터를 비동기로 호출합니다.

### 4. 면접 진행 페이지 ([/src/pages/interview/InterviewPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/interview/InterviewPage.jsx))
*   **핵심 로직**: 실제 AI 면접 세션을 진행하는 페이지입니다.
*   **주요 기능 및 기술**:
    *   **WebRTC / Media Streams**: `navigator.mediaDevices.getUserMedia`를 사용하여 카메라와 마이크에 접근합니다.
    *   **MediaRecorder API**: 음성을 녹음하여 청크(Chunk) 단위로 캡처하고 STT 처리를 위해 사용합니다.
    *   **타이머 로직**: `setInterval`을 사용하여 답변 제한 시간을 카운트다운합니다.
    *   **실시간 피드백**: 녹음 상태(`LIVE REC`)를 시각적으로 표시합니다.

### 5. 이력서 업로드 페이지 ([/src/pages/landing/ResumePage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/landing/ResumePage.jsx))
*   **핵심 로직**: PDF 이력서를 업로드하고 내용을 분석합니다.
*   **주요 기능 및 기술**:
    *   **폴링 (Polling) 패턴**: 이력서 분석이 완료될 때까지 `setTimeout`을 이용한 재귀 호출로 서버 상태를 주기적으로 확인합니다.
    *   **파일 처리**: PDF 파일 형식 및 크기를 검증합니다.

### 6. 프로필 관리 페이지 ([/src/pages/profile/ProfileManagementPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/profile/ProfileManagementPage.jsx))
*   **핵심 로직**: 사용자 개인 정보 및 희망 직무 정보를 수정합니다.
*   **주요 기능 및 기술**:
    *   **다중 선택 로직**: 희망 기업 형태 및 직무를 배열(Array) 상태로 관리하며 토글(Toggle) 방식으로 구현했습니다.
    *   **이미지 업로드**: 프로필 사진 변경 시 `FileReader`를 사용합니다.

### 7. 결과 분석 페이지 ([/src/pages/result/ResultPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/result/ResultPage.jsx))
*   **핵심 로직**: 면접 결과 점수와 상세 분석 내용을 시각화하여 보여줍니다.
*   **주요 라이브러리**:
    *   **Recharts**: 레이더 차트(`RadarChart`)를 사용하여 역량별 점수를 시각화했습니다.
    *   **html2canvas**: 리포트 화면(DOM)을 캡처하여 이미지로 변환합니다.
    *   **jsPDF**: 캡처된 이미지를 포함한 PDF 파일을 생성하고 다운로드 기능을 제공합니다.

### 8. 계정 설정 페이지 ([/src/pages/settings/AccountSettingsPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/settings/AccountSettingsPage.jsx))
*   **핵심 로직**: 비밀번호 변경 및 알림 설정을 관리합니다.
*   **주요 기능 및 기술**:
    *   **폼 유효성 검사**: 비밀번호 복잡도 및 일치 여부를 검사합니다.
    *   **아코디언 UI**: 이용약관 및 개인정보 처리방침을 토글 형태로 보여줍니다.

### 9. 환경 테스트 페이지 ([/src/pages/setup/EnvTestPage.jsx](file:///c:/big20/git/Big20_aI_interview_project/frontend/src/pages/setup/EnvTestPage.jsx))
*   **핵심 로직**: 면접 전 카메라와 마이크가 정상 작동하는지 테스트합니다.
*   **주요 기능 및 기술**:
    *   **Web Audio API**: `AudioContext`, `AnalyserNode`를 사용하여 마이크 입력 볼륨을 실시간으로 시각화합니다.
    *   **얼굴 인식 시뮬레이션**: 프론트엔드에서 얼굴 인식 UI 흐름을 시뮬레이션합니다.
    *   **Deepgram SDK / API**: `@deepgram/sdk`를 사용하여 음성 인식(STT) 기능을 테스트합니다.
