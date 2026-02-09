

```
mermaid
flowchart TD
    Start([SD 시작]) --> A{UI/UX 설계<br/>필요한가?}
  
    A -->|Yes| B[사용자 플로우 정의]
    A -->|No| C[기존 설계 활용]
  
    B --> D[화면 구조 설계<br/>- 메인 화면<br/>- 면접 화면<br/>- 결과 화면]
    C --> D
  
    D --> E[와이어프레임 작성]
  
    E --> F{와이어프레임<br/>승인?}
    F -->|No| D
    F -->|Yes| G[기술 스택 결정]
  
    G --> H{기술 스택<br/>확정?}
    H -->|No| I[기술 검토<br/>- Streamlit vs Flask<br/>- DB 선택<br/>- 배포 방식]
    I --> G
  
    H -->|Yes| J[개발 환경 구축<br/>- Git Repository<br/>- 가상환경<br/>- 패키지 설치]
  
    J --> K{환경 구축<br/>완료?}
    K -->|No| J
    K -->|Yes| L[Sprint 1 시작<br/>목표: 기본 UI]
  
    L --> M{어떤 화면부터<br/>개발?}
    M -->|메인| N1[메인 화면 개발<br/>- 제목<br/>- 입력 폼<br/>- 시작 버튼]
    M -->|면접| N2[면접 화면 개발<br/>- 질문 영역<br/>- 답변 입력<br/>- 제출 버튼]
    M -->|결과| N3[결과 화면 개발<br/>- 점수 표시<br/>- 피드백<br/>- 재시작]
  
    N1 --> O[입력 검증 추가]
    N2 --> O
    N3 --> O
  
    O --> P{Sprint 1<br/>테스트}
    P -->|실패| Q[버그 수정<br/>문제점 기록]
    Q --> M
  
    P -->|통과| R[Sprint 2 시작<br/>목표: API 연동]
  
    R --> S{MA 프롬프트<br/>준비 완료?}
    S -->|No| T[MA 팀과 협의<br/>프롬프트 전달 요청]
    T --> S
  
    S -->|Yes| U[OpenAI API<br/>클라이언트 초기화]
  
    U --> V[질문 생성 API<br/>함수 구현]
  
    V --> W{질문 생성<br/>테스트}
    W -->|실패| X[디버깅<br/>- API 키 확인<br/>- 프롬프트 확인<br/>- 파라미터 확인]
    X --> V
  
    W -->|성공| Y[답변 평가 API<br/>함수 구현]
  
    Y --> Z{평가 기능<br/>테스트}
    Z -->|실패| AA[디버깅<br/>- JSON 파싱<br/>- 점수 추출<br/>- 에러 처리]
    AA --> Y
  
    Z -->|성공| AB[에러 처리 구현]
  
    AB --> AC{에러 시나리오<br/>처리 완료?}
    AC -->|No| AD[에러 케이스 추가<br/>- Timeout<br/>- Rate Limit<br/>- Network Error]
    AD --> AB
  
    AC -->|Yes| AE[Sprint 2 테스트]
  
    AE --> AF{API 연동<br/>정상 작동?}
    AF -->|No| AG[문제 분석<br/>- API 호출<br/>- 응답 처리<br/>- 에러 핸들링]
    AG --> R
  
    AF -->|Yes| AH[Sprint 3 시작<br/>목표: 통합]
  
    AH --> AI[UI와 API 통합]
  
    AI --> AJ[상태 관리 구현<br/>- Session State<br/>- 대화 기록<br/>- 진행 상황]
  
    AJ --> AK[전체 플로우 연결<br/>시작→질문→답변→평가→결과]
  
    AK --> AL{통합 테스트}
    AL -->|실패| AM[통합 문제 해결<br/>- 데이터 흐름<br/>- 화면 전환<br/>- 상태 동기화]
    AM --> AI
  
    AL -->|성공| AN[성능 최적화<br/>- 로딩 시간<br/>- 캐싱<br/>- UX 개선]
  
    AN --> AO[사용자 테스트 준비]
  
    AO --> AP{테스터<br/>섭외 완료?}
    AP -->|No| AQ[테스터 모집<br/>5명 목표]
    AQ --> AP
  
    AP -->|Yes| AR[사용자 테스트 진행]
  
    AR --> AS[피드백 수집<br/>- 사용성<br/>- 버그<br/>- 개선 아이디어]
  
    AS --> AT{주요 이슈<br/>있나?}
    AT -->|Yes| AU[우선순위 결정<br/>Critical/Major/Minor]
    AU --> AV{수정 필요?}
    AV -->|Critical| AI
    AV -->|Major| AN
    AV -->|Minor| AW[백로그 기록]
  
    AT -->|No| AW
    AW --> AX[최종 완성]
  
    AX --> AY[배포 준비<br/>- 코드 정리<br/>- 주석 추가<br/>- README 작성]
  
    AY --> AZ{배포 체크리스트<br/>완료?}
    AZ -->|No| BA[누락 항목 확인<br/>- GitHub 업로드<br/>- 문서화<br/>- 시연 영상]
    BA --> AY
  
    AZ -->|Yes| BB[GitHub 업로드]
  
    BB --> BC[시연 영상 제작<br/>- 시나리오 작성<br/>- 녹화<br/>- 편집]
  
    BC --> BD{최종 점검<br/>완료?}
    BD -->|No| BE[체크리스트 확인<br/>- 기능 동작<br/>- 문서 완성<br/>- 발표 준비]
    BE --> BD
  
    BD -->|Yes| End([SD 완료])
  
    style Start fill:#e1f5e1
    style End fill:#ffe1e1
    style P fill:#e1e5ff
    style AF fill:#e1e5ff
    style AL fill:#e1e5ff
    style AT fill:#fff4e1
```
