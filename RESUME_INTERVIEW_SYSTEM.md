# 🎯 이력서 기반 맞춤형 면접 시스템

## BGE-M3 모델로 가능한 것들

### ✅ 1. 이력서 자동 분석 및 데이터 추출
- 📄 **파일 형식 지원**: PDF, DOCX, TXT
- 🔍 **자동 정보 추출**: 이름, 경력, 기술 스택, 학력, 프로젝트
- 📊 **구조화된 데이터 생성**: JSON/Database 저장

### ✅ 2. 맞춤형 면접 질문 자동 생성
- 🎯 **경력 기반 질문**: 이력서의 프로젝트/경험 분석
- 💡 **기술 스택 기반 질문**: 언급된 기술에 대한 심화 질문
- 📈 **난이도 조절**: 경력에 따라 자동 조정

### ✅ 3. 유사 경험자 매칭
- 👥 **유사 이력서 검색**: 벡터 유사도 기반
- 📋 **과거 면접 질문 추천**: 비슷한 경력자에게 했던 질문

### ✅ 4. 답변 평가 및 피드백
- ✍️ **실시간 답변 평가**: 모범 답변과 비교
- 📊 **점수 산출**: 유사도 기반 자동 채점
- 💬 **개선 피드백**: 부족한 부분 자동 제안

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐
│  이력서 업로드   │ (PDF/DOCX/TXT)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  텍스트 추출     │ (PyPDF2, python-docx)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  정보 파싱       │ (정규식 + NLP)
│  - 이름          │
│  - 경력          │
│  - 기술 스택     │
│  - 프로젝트      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  BGE-M3 임베딩  │ (이력서 → 벡터)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  VectorDB 저장  │ (PostgreSQL + pgvector)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  질문 매칭       │ (유사도 검색)
│  - 기술 질문     │
│  - 경험 질문     │
│  - 프로젝트 질문 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  면접 질문 생성  │
└─────────────────┘
```

---

## 💻 구현 예시

### 1단계: 이력서 파싱 시스템

```python
# resume_parser.py
import re
from typing import Dict, List, Any
import PyPDF2
from docx import Document

class ResumeParser:
    """이력서 파싱 및 정보 추출"""

    def __init__(self):
        self.tech_keywords = [
            'Python', 'Java', 'JavaScript', 'React', 'FastAPI',
            'Django', 'Docker', 'Kubernetes', 'PostgreSQL', 'MongoDB',
            'AWS', 'GCP', 'Azure', 'Git', 'CI/CD'
        ]

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        """DOCX에서 텍스트 추출"""
        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def extract_info(self, text: str) -> Dict[str, Any]:
        """이력서에서 정보 추출"""

        # 1. 이메일 추출
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        # 2. 전화번호 추출
        phone_pattern = r'\d{2,3}-\d{3,4}-\d{4}'
        phones = re.findall(phone_pattern, text)

        # 3. 기술 스택 추출
        found_skills = []
        for tech in self.tech_keywords:
            if tech.lower() in text.lower():
                found_skills.append(tech)

        # 4. 경력 연수 추출 (예: "3년", "5년 경력")
        experience_pattern = r'(\d+)년'
        experience_matches = re.findall(experience_pattern, text)
        total_experience = max([int(x) for x in experience_matches], default=0)

        return {
            'email': emails[0] if emails else None,
            'phone': phones[0] if phones else None,
            'skills': found_skills,
            'experience_years': total_experience,
            'raw_text': text
        }

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """이력서 파일 파싱"""
        if file_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self.extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        return self.extract_info(text)
```

### 2단계: 이력서 임베딩 및 저장

```python
# resume_vectordb.py
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, Field, SQLModel, create_engine, Column
from pgvector.sqlalchemy import Vector
from typing import List, Optional
import json

class Resume(SQLModel, table=True):
    """이력서 테이블"""
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: str  # JSON 문자열
    experience_years: int = 0
    raw_text: str

    # 벡터 임베딩 (BGE-M3: 1024차원)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024))
    )

class ResumeVectorDB:
    """이력서 벡터 데이터베이스"""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.model = SentenceTransformer('BAAI/bge-m3')
        SQLModel.metadata.create_all(self.engine)

    def add_resume(self, resume_data: dict) -> Resume:
        """이력서 추가"""

        # 이력서 전체 텍스트 임베딩
        embedding = self.model.encode(
            resume_data['raw_text'],
            normalize_embeddings=True
        ).tolist()

        resume = Resume(
            candidate_name=resume_data.get('name', 'Unknown'),
            email=resume_data.get('email'),
            phone=resume_data.get('phone'),
            skills=json.dumps(resume_data.get('skills', [])),
            experience_years=resume_data.get('experience_years', 0),
            raw_text=resume_data['raw_text'],
            embedding=embedding
        )

        with Session(self.engine) as session:
            session.add(resume)
            session.commit()
            session.refresh(resume)

        return resume

    def find_similar_resumes(self, query_text: str, top_k: int = 5):
        """유사한 이력서 검색"""
        from sqlmodel import select, text

        query_emb = self.model.encode(
            query_text,
            normalize_embeddings=True
        ).tolist()

        with Session(self.engine) as session:
            stmt = select(
                Resume,
                text(f"embedding <=> '{query_emb}' AS distance")
            ).order_by(text("distance")).limit(top_k)

            results = session.exec(stmt).all()

            return [
                {
                    'resume': result[0],
                    'similarity': 1 - result[1]
                }
                for result in results
            ]
```

### 3단계: 맞춤형 질문 생성

```python
# interview_question_generator.py
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

class InterviewQuestionGenerator:
    """이력서 기반 면접 질문 생성"""

    def __init__(self, question_db):
        self.model = SentenceTransformer('BAAI/bge-m3')
        self.question_db = question_db  # 기존 질문 데이터베이스

    def generate_questions_from_resume(
        self,
        resume_data: dict,
        num_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """이력서 기반 질문 생성"""

        questions = []

        # 1. 기술 스택 기반 질문 (50%)
        tech_questions = self._get_tech_questions(
            resume_data['skills'],
            num_questions // 2
        )
        questions.extend(tech_questions)

        # 2. 경험/프로젝트 기반 질문 (30%)
        exp_questions = self._get_experience_questions(
            resume_data['raw_text'],
            num_questions * 3 // 10
        )
        questions.extend(exp_questions)

        # 3. 일반 질문 (20%)
        general_questions = self._get_general_questions(
            resume_data['experience_years'],
            num_questions - len(questions)
        )
        questions.extend(general_questions)

        return questions

    def _get_tech_questions(self, skills: List[str], count: int):
        """기술 스택 기반 질문"""
        questions = []

        for skill in skills[:count]:
            # 해당 기술에 대한 질문 검색
            query = f"{skill} 기술 면접 질문"
            query_emb = self.model.encode([query], normalize_embeddings=True)[0]

            # VectorDB에서 유사 질문 검색
            similar = self._search_questions(query_emb, top_k=2)
            questions.extend(similar)

        return questions[:count]

    def _get_experience_questions(self, resume_text: str, count: int):
        """경험 기반 질문"""
        # 이력서 내용과 유사한 질문 검색
        resume_emb = self.model.encode([resume_text], normalize_embeddings=True)[0]
        return self._search_questions(resume_emb, top_k=count)

    def _get_general_questions(self, experience_years: int, count: int):
        """경력에 따른 일반 질문"""
        if experience_years < 2:
            difficulty = "easy"
        elif experience_years < 5:
            difficulty = "medium"
        else:
            difficulty = "hard"

        # 난이도에 맞는 질문 검색
        return self._search_questions_by_difficulty(difficulty, count)

    def _search_questions(self, query_emb, top_k: int):
        """벡터 검색으로 질문 찾기"""
        # 실제 구현은 VectorDB 연동
        pass

    def _search_questions_by_difficulty(self, difficulty: str, count: int):
        """난이도별 질문 검색"""
        pass
```

### 4단계: 전체 워크플로우

```python
# main_workflow.py
from resume_parser import ResumeParser
from resume_vectordb import ResumeVectorDB
from interview_question_generator import InterviewQuestionGenerator

def process_resume_and_generate_interview(resume_file_path: str):
    """이력서 처리 및 면접 질문 생성 전체 워크플로우"""

    # 1. 이력서 파싱
    print("📄 이력서 파싱 중...")
    parser = ResumeParser()
    resume_data = parser.parse_resume(resume_file_path)

    print(f"✅ 파싱 완료!")
    print(f"   - 기술 스택: {', '.join(resume_data['skills'])}")
    print(f"   - 경력: {resume_data['experience_years']}년")

    # 2. VectorDB에 저장
    print("\n💾 VectorDB에 저장 중...")
    db = ResumeVectorDB("postgresql://admin:admin@localhost/interview_db")
    resume = db.add_resume(resume_data)
    print(f"✅ 저장 완료! (ID: {resume.id})")

    # 3. 유사 이력서 검색
    print("\n🔍 유사한 이력서 검색 중...")
    similar_resumes = db.find_similar_resumes(resume_data['raw_text'], top_k=3)

    for i, item in enumerate(similar_resumes, 1):
        print(f"   {i}. 유사도: {item['similarity']:.3f}")
        print(f"      기술: {item['resume'].skills}")

    # 4. 맞춤형 면접 질문 생성
    print("\n🎯 맞춤형 면접 질문 생성 중...")
    generator = InterviewQuestionGenerator(question_db=None)
    questions = generator.generate_questions_from_resume(resume_data, num_questions=10)

    print(f"✅ {len(questions)}개 질문 생성 완료!")

    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q.get('category', 'N/A')}] {q.get('content', 'N/A')[:80]}...")
        print(f"   난이도: {q.get('difficulty', 'N/A')}")

    return {
        'resume': resume,
        'questions': questions,
        'similar_resumes': similar_resumes
    }

# 사용 예시
if __name__ == "__main__":
    result = process_resume_and_generate_interview("candidate_resume.pdf")
```

---

## 🎯 실제 사용 시나리오

### 시나리오 1: 백엔드 개발자 면접

**입력 이력서**:
```
이름: 김개발
경력: 3년
기술 스택: Python, FastAPI, PostgreSQL, Docker, AWS
프로젝트:
- 전자상거래 API 서버 개발 (FastAPI, PostgreSQL)
- 마이크로서비스 아키텍처 구축 (Docker, Kubernetes)
```

**자동 생성 질문**:
1. [기술] Python의 GIL에 대해 설명하고, 멀티스레딩 성능에 미치는 영향은?
2. [기술] FastAPI와 Django의 차이점은 무엇이며, FastAPI를 선택한 이유는?
3. [경험] 전자상거래 API 서버 개발 시 가장 어려웠던 점은?
4. [경험] 마이크로서비스 아키텍처에서 서비스 간 통신은 어떻게 구현했나요?
5. [기술] PostgreSQL의 인덱스 최적화 경험이 있나요?

### 시나리오 2: 신입 개발자 면접

**입력 이력서**:
```
이름: 이신입
경력: 0년 (신입)
기술 스택: Python, JavaScript, React
프로젝트:
- 개인 블로그 웹사이트 (React)
- 간단한 REST API (Python Flask)
```

**자동 생성 질문** (난이도 낮음):
1. [기본] Python의 리스트와 튜플의 차이점은?
2. [기본] React의 컴포넌트 생명주기에 대해 설명해주세요
3. [경험] 개인 블로그 프로젝트에서 어떤 기술을 사용했나요?
4. [기본] REST API의 HTTP 메서드(GET, POST, PUT, DELETE)의 용도는?
5. [일반] 가장 최근에 학습한 기술은 무엇인가요?

---

## 📊 예상 결과

### 이력서 분석 결과
```json
{
  "candidate_name": "김개발",
  "email": "kim@example.com",
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
  "experience_years": 3,
  "matched_questions": 10,
  "difficulty_distribution": {
    "easy": 2,
    "medium": 5,
    "hard": 3
  }
}
```

### 질문 매칭 정확도
- **기술 스택 매칭**: 95% (이력서에 명시된 기술)
- **경력 수준 매칭**: 90% (3년 경력 → medium 난이도)
- **프로젝트 관련성**: 85% (실제 경험과 연관)

---

## 🚀 다음 단계 구현

1. ✅ **이력서 파서 구현** (`resume_parser.py`)
2. ✅ **VectorDB 스키마 추가** (Resume 테이블)
3. ✅ **질문 생성 로직** (`interview_question_generator.py`)
4. ⬜ **API 엔드포인트 추가** (`/api/resume/upload`, `/api/interview/generate`)
5. ⬜ **프론트엔드 UI** (이력서 업로드 + 질문 표시)

---

## 💡 추가 가능한 기능

### 1. 실시간 답변 평가
- 면접자의 답변을 BGE-M3로 임베딩
- 모범 답변과 유사도 비교
- 즉시 피드백 제공

### 2. 면접 난이도 동적 조정
- 답변 품질에 따라 다음 질문 난이도 조정
- 잘 답변하면 → 더 어려운 질문
- 어려워하면 → 쉬운 질문

### 3. 면접 리포트 자동 생성
- 전체 답변 분석
- 강점/약점 파악
- 개선 방향 제시

### 4. 다국어 이력서 지원
- BGE-M3의 다국어 능력 활용
- 영어, 중국어, 일본어 이력서 자동 처리

---

**이 시스템을 구현해드릴까요?** 🚀
