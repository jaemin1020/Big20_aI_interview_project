# 실제 AI 이력서 구조 기반 파서 완성

## 📋 실제 이력서 구조

### 원본 이력서 구성
```
1. 개인 정보
   - 이름, 주소, 전화번호, 이메일
   
2. 지원 정보
   - 지원 직무
   - 지원 회사
   
3. 경력
   - 회사명, 위치, 직책
   - 근무 기간
   - 업무 내용
   - 사용 기술
   
4. 학력
   - 대학교 (전공, 학위, 졸업년도)
   - 고등학교
   
5. 자격증
   - 자격증명 (쉼표로 구분)
   
6. 프로젝트
   - 프로젝트명
   - 설명
   - 사용 기술
   
7. 기술 스택
   - 보안 기술 (Network 패킷 분석, Wireshark, 방화벽 등)
   
8. 언어 능력
   - 영어 (TOEIC 점수)
   - 일본어 (JLPT 레벨)
   
9. 자기소개서
   - 성장과정
   - 성격의 장단점
   - 지원동기
   - 입사후포부
```

---

## ✅ 파싱 결과 (structured_resume.json)

```json
{
  "personal_info": {
    "name": "최승우",
    "address": "경기도 성남시 분당구 판교역로",
    "phone": "+82 10-5544-2211",
    "email": "sw_choi.security@vmail.com"
  },
  "target_position": {
    "position": "보안엔지니어",
    "company": "안랩"
  },
  "experience": [
    {
      "company": "한국인터넷진흥원(KISA)",
      "location": "서울",
      "position": "인턴",
      "duration": "2023년 7월 ~ 2023년 8월",
      "description": "Network 패킷 분석(Wireshark) 공공기관 보안 관제 시스템 모니터링...",
      "tech_stack": ["Wireshark"]
    }
  ],
  "education": [
    {
      "school": "세종대학교",
      "degree": "학사",
      "major": "정보보호학",
      "graduation_date": null
    }
  ],
  "certifications": [
    {"name": "정보보안기사"},
    {"name": "리눅스마스터 2급"},
    {"name": "네트워크관리사 2급"}
  ],
  "projects": [
    {
      "name": "오픈소스 기반 침입 탐지 시스템(IDS) 구축 프로젝트",
      "description": "Snort를 활용하여 학내 가상 네트워크망의 비정상 트래픽을 실시간으로 탐지..."
    }
  ],
  "skills": {
    "security": [
      "Network 패킷 분석",
      "Wireshark",
      "리눅스 시스템 관리",
      "방화벽",
      "악성코드 분석",
      "IDS",
      "Snort",
      "침입 탐지"
    ]
  },
  "languages": [
    {"language": "영어", "proficiency": "TOEIC 850점"},
    {"language": "일본어", "proficiency": "JLPT N2"}
  ],
  "cover_letter": {
    "growth_process": "정직함이 최고의 방어막이라는 가르침 아래 성장했습니다...",
    "personality": "저는 매우 꼼꼼하고 규칙 준수를 철저히 하는 성격입니다...",
    "motivation": "안랩은 대한민국 보안의 자부심이자 가장 신뢰받는 기업입니다...",
    "aspiration": "입사 초기에는 안랩의 위협 분석 시스템을 빠르게 익히고..."
  }
}
```

---

## 🔧 구현 파일

### `ai-worker/utils/resume_structurer_v2.py`

**주요 기능**:
1. ✅ **개인 정보 추출** (`_extract_personal_info`)
   - 이름, 주소, 전화번호, 이메일
   
2. ✅ **지원 정보 추출** (`_extract_target_position`)
   - 지원 직무, 지원 회사
   
3. ✅ **경력 추출** (`_extract_experience`)
   - 회사명, 위치, 직책, 기간, 업무 내용, 기술스택
   
4. ✅ **학력 추출** (`_extract_education`)
   - 대학교, 고등학교 (전공, 학위, 졸업년도)
   
5. ✅ **자격증 추출** (`_extract_certifications`)
   - 자격증명 리스트
   
6. ✅ **프로젝트 추출** (`_extract_projects`)
   - 프로젝트명, 설명, 기술스택
   
7. ✅ **기술 스택 추출** (`_extract_skills`)
   - 보안 기술 키워드 자동 추출
   
8. ✅ **언어 능력 추출** (`_extract_languages`)
   - TOEIC, JLPT 점수 파싱
   
9. ✅ **자기소개서 추출** (`_extract_cover_letter`)
   - 성장과정, 성격, 지원동기, 입사후포부

---

## 💻 사용 방법

### 1. PDF → 텍스트 추출
```python
from utils.pdf_parser import ResumePDFParser

text = ResumePDFParser.extract_text("AI 이력서.pdf")
```

### 2. 텍스트 → 구조화
```python
from utils.resume_structurer_v2 import ResumeStructurerV2

structurer = ResumeStructurerV2()
structured = structurer.structure_resume(text)
```

### 3. 전체 파이프라인 (Celery Task)
```python
# ai-worker/tasks/resume_parser.py 업데이트 필요
from utils.resume_structurer_v2 import ResumeStructurerV2

# 기존 코드에서 변경
# structurer = ResumeStructurer()  # 기존
structurer = ResumeStructurerV2()  # 신규
structured_data = structurer.structure_resume(cleaned_text)
```

---

## 🎯 ResumeTool 업데이트

### `ai-worker/tools/resume_tool.py` 개선

```python
def format_for_llm(resume_info: Dict) -> str:
    """LLM 프롬프트용 포맷팅 (실제 구조 반영)"""
    
    if not resume_info.get("has_resume"):
        return "이력서 정보 없음"
    
    structured = resume_info.get("structured_data", {})
    parts = []
    
    # 개인 정보
    if "personal_info" in structured:
        info = structured["personal_info"]
        parts.append(f"【 지원자 정보 】")
        parts.append(f"이름: {info.get('name', 'N/A')}")
        parts.append(f"이메일: {info.get('email', 'N/A')}")
        parts.append("")
    
    # 지원 정보
    if "target_position" in structured:
        target = structured["target_position"]
        parts.append(f"【 지원 정보 】")
        parts.append(f"지원 직무: {target.get('position', 'N/A')}")
        parts.append(f"지원 회사: {target.get('company', 'N/A')}")
        parts.append("")
    
    # 경력
    if "experience" in structured and structured["experience"]:
        parts.append("【 경력 】")
        for i, exp in enumerate(structured["experience"], 1):
            parts.append(f"{i}. {exp.get('company', 'N/A')} - {exp.get('position', 'N/A')}")
            parts.append(f"   기간: {exp.get('duration', 'N/A')}")
            parts.append(f"   업무: {exp.get('description', '')[:200]}")
            if exp.get('tech_stack'):
                parts.append(f"   기술: {', '.join(exp['tech_stack'])}")
        parts.append("")
    
    # 학력
    if "education" in structured and structured["education"]:
        parts.append("【 학력 】")
        for edu in structured["education"]:
            parts.append(f"  {edu.get('school', 'N/A')} - {edu.get('major', 'N/A')} {edu.get('degree', '')}")
        parts.append("")
    
    # 자격증
    if "certifications" in structured and structured["certifications"]:
        parts.append("【 자격증 】")
        for cert in structured["certifications"]:
            parts.append(f"  - {cert.get('name', 'N/A')}")
        parts.append("")
    
    # 프로젝트
    if "projects" in structured and structured["projects"]:
        parts.append("【 프로젝트 】")
        for i, proj in enumerate(structured["projects"], 1):
            parts.append(f"{i}. {proj.get('name', 'N/A')}")
            if proj.get('description'):
                parts.append(f"   {proj['description'][:150]}...")
        parts.append("")
    
    # 기술 스택
    if "skills" in structured and structured["skills"].get("security"):
        parts.append("【 보안 기술 】")
        parts.append(f"  {', '.join(structured['skills']['security'])}")
        parts.append("")
    
    # 언어 능력
    if "languages" in structured and structured["languages"]:
        parts.append("【 언어 능력 】")
        for lang in structured["languages"]:
            parts.append(f"  {lang.get('language', 'N/A')}: {lang.get('proficiency', 'N/A')}")
        parts.append("")
    
    # 자기소개서 (지원동기 중심)
    if "cover_letter" in structured:
        cl = structured["cover_letter"]
        if cl.get("motivation"):
            parts.append("【 지원 동기 】")
            parts.append(cl["motivation"][:300] + "...")
            parts.append("")
    
    return "\n".join(parts)
```

---

## 📊 질문 생성 예시

### 이력서 기반 맞춤형 질문

```python
from tools import ResumeTool

resume_info = ResumeTool.get_resume_by_interview(interview_id=10)

# 생성될 질문 예시:
# 1. "KISA에서 인턴으로 근무하며 Wireshark를 사용한 패킷 분석 경험이 있는데, 
#     가장 기억에 남는 위협 분석 사례를 설명해주세요."
#
# 2. "IDS 구축 프로젝트에서 Snort를 활용하셨는데, 
#     비정상 트래픽 탐지 시 어떤 룰을 주로 사용하셨나요?"
#
# 3. "안랩의 인재상과 본인의 경험을 연결하여 설명해주세요."
#
# 4. "정보보안기사 자격증을 보유하고 계신데, 
#     실무에서 가장 유용했던 지식은 무엇인가요?"
```

---

## ✅ 완료 사항

1. ✅ PDF 텍스트 추출 (`pdf_parser.py`)
2. ✅ 실제 이력서 구조 분석
3. ✅ 구조화 파서 구현 (`resume_structurer_v2.py`)
4. ✅ 9개 섹션 파싱 완료
   - 개인정보, 지원정보, 경력, 학력, 자격증, 프로젝트, 기술, 언어, 자기소개서
5. ✅ JSON 출력 검증

---

## 🚀 다음 단계

1. **Celery Task 업데이트**
   - `resume_parser.py`에서 `ResumeStructurerV2` 사용
   
2. **ResumeTool 업데이트**
   - `format_for_llm` 함수 개선
   
3. **질문 생성 개선**
   - 자기소개서 내용 활용
   - 지원 회사 맞춤형 질문

---

**작성일**: 2026-01-29  
**버전**: 2.0 (실제 이력서 구조 반영)
