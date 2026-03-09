# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

C:\big20\Big20_aI_interview_project\파이널_진행보고서\면접준비\프로젝트소개.md여기서 프론트엔드에 react는 무슨 역할이야

*Viewed [프로젝트소개.md](file:///c:/big20/Big20_aI_interview_project/%ED%8C%8C%EC%9D%B4%EB%84%90_%EC%A7%84%ED%96%89%EB%B3%B4%EA%B3%A0%EC%84%9C/%EB%A9%B4%EC%A0%91%EC%A4%80%EB%B9%84/%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%EC%86%8C%EA%B0%9C.md) *

*Listed directory [Big20_aI_interview_project](file:///c:/big20/Big20_aI_interview_project) *

*Listed directory [frontend](file:///c:/big20/Big20_aI_interview_project/frontend) *

*Viewed [package.json](file:///c:/big20/Big20_aI_interview_project/frontend/package.json) *

### Planner Response

`프로젝트소개.md` 문서와 실제 프론트엔드([package.json](cci:7://file:///c:/big20/Big20_aI_interview_project/frontend/package.json:0:0-0:0) 등) 소스 코드를 종합해 볼 때, 이 프로젝트에서 **React**는 단순히 화면을 보여주는 것을 넘어 **"실시간 멀티모달 인터랙티브 엔진"**의 중추적인 역할을 담당하고 있습니다.

구체적인 역할은 다음과 같이 5가지 핵심 포인트로 요약할 수 있습니다.

### 1. 복잡한 인터랙티브 UI의 컴포넌트화 (Component Architecture)
AI 면접 시스템은 **실시간 비디오 피드, 스트리밍 되는 질문 텍스트, 타이머, 실시간 감정 분석 차트** 등 매우 dynamic한 요소들이 한 화면에 모여 있습니다.
*   React를 사용해 이 각각의 요소들을 독립적인 **컴포넌트**로 관리함으로써, 전체 페이지를 다시 그리지 않고도 질문이 바뀌거나 분석 결과가 업데이트될 때 해당 부분만 효율적으로 렌더링합니다.

### 2. 정교한 면접 프로세스 상태 관리 (State Management)
면접은 `준비(Registration) -> 진행(Interviewing) -> 실시간 분석(Analysis) -> 결과 리포트(Report)`라는 엄격한 단계별 흐름을 가집니다.
*   **React Router**를 통해 각 단계별 페이지 전환을 관리하고, React의 **State**를 활용해 현재 지원자가 몇 번째 질문에 답하고 있는지, 마이크/카메라 권한은 허용되었는지 등의 복잡한 상태를 실시간으로 추적합니다.

### 3. 실시간 통신 및 스트리밍 제어 (Real-time Streaming & Socket.io)
이 프로젝트의 핵심은 **실시간성**입니다.
*   **Socket.io-client**: 백엔드(FastAPI)와 상시 연결을 유지하며, AI가 생성한 질문을 실시간으로 수신하거나 면접 상태를 즉각적으로 업데이트합니다.
*   **Media Stream API**: 브라우저의 카메라와 마이크 권한을 제어하고, 수집된 영상/음성 데이터를 백엔드로 스트리밍하여 시선 추적 및 표정 분석이 가능하게 합니다.

### 4. 클라이언트 사이드 음성 처리 (Deepgram STT 연동)
[package.json](cci:7://file:///c:/big20/Big20_aI_interview_project/frontend/package.json:0:0-0:0)을 보면 `@deepgram/sdk`가 포함되어 있습니다.
*   지원자의 음성을 실시간으로 텍스트로 변환(STT)할 때, 서버에만 의존하지 않고 **React 클라이언트 단에서 직접 Deepgram API와 통신**하여 지연 시간을 최소화하고 더 빠른 피드백을 제공합니다.

### 5. 데이터 시각화 및 결과서 생성 (Data Visualization & PDF)
면접이 끝난 후 지원자의 역량을 한눈에 보여주는 역할을 합니다.
*   **Recharts**: 수집된 감정 데이터나 시선 처리 데이터를 사용자가 이해하기 쉬운 그래프와 차트로 시각화합니다.
*   **jspdf / html2canvas**: 웹 화면에 렌더링 된 분석 결과를 즉석에서 PDF 파일로 변환하여 사용자가 리포트를 소장할 수 있게 합니다.

---

**요약하자면:**
React는 이 프로젝트에서 **"사용자의 입력을 실시간으로 수집하고, AI의 처리 결과를 가장 빠르고 직관적으로 전달하는 인터랙티브 허브"** 역할을 하고 있습니다. `프로젝트소개.md`에서 언급된 "실시간 영상/음성 스트리밍 수집"과 "인터랙티브한 환경" 이라는 설명이 바로 이러한 React의 기능들을 통해 구현된 것입니다.