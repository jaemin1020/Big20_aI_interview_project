 Git Commit Message Convention
 본 프로젝트는 코드 이력의 가독성과 유지보수 효율을 위해 Conventional Commits 및 Angular Commit Message Guideline을 준수합니다.

1. 커밋 메시지 구조기본적인 커밋 메시지 구조는 아래와 같습니다.
<<<<<<< HEAD
   Plaintext
   type(scope): subject
=======

```plaintext
type(username): subject
>>>>>>> main

body

footer
<<<<<<< HEAD
=======
```


>>>>>>> main
2. 제목 규칙 (Subject)
제목은 변경 사항을 요약하며, 50자 이내로 작성합니다.
Type (유형)유형설명
feat 새로운 기능 추가
fix 버그 수정
docs 문서 수정 (README, 주석 등)
style 코드 의미에 영향을 주지 않는 변경 (포맷팅, 세미콜론 누락 등)
refactor 코드 리팩토링 (기능 변화 없이 코드 구조만 개선)
test 테스트 코드 추가 및 수정
chore 빌드 업무, 패키지 매니저 설정, 환경 설정 변경

Subject 상세첫 글자는 대문자로 시작합니다.
끝에 **마침표(.)**를 찍지 않습니다.
명령문 형태를 사용합니다. (예: Add feature O / Added feature X)

3. 본문 규칙 (Body)
   무엇을, 왜 변경했는지에 대해 상세히 설명합니다.
   한 줄당 72자를 넘기지 않도록 줄바꿈을 권장합니다.
   제목만으로 설명이 충분한 경우 생략 가능합니다.
4. 바닥글 규칙 (Footer)이슈 트래커 ID(Issue Tracker ID)를 참조할 때 사용합니다.
   예시: Fixes: #123, Related to: #456
   5.작성 가이드라인 (The Seven Rules)
   제목과 본문을 한 줄 띄워 분리합니다.
   제목은 50자 이내로 제한합니다.
   제목 첫 글자를 대문자로 시작합니다.
   제목 끝에 마침표를 찍지 않습니다.
   제목은 명령문으로 작성합니다.
   본문은 72자마다 줄 바꿈을 수행합니다.
   본문은 '어떻게'보다 **'무엇을', '왜'**에 집중합니다.
5. 예시 (Example)
<<<<<<< HEAD
   Plaintext
   feat(auth): Add Google OAuth2 login functionality

Implement the OAuth2 flow to allow users to sign in with Google.
This includes updating the user schema to store provider IDs.

Ref: #104
=======

```Plaintext

feat(auth): Add Google OAuth2 login functionality
Implement the OAuth2 flow to allow users to sign in with Google.
This includes updating the user schema to store provider
 IDs.Ref: #104
```
>>>>>>> main
