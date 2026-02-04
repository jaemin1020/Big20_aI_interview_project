"""
이력서 파서 (Resume Parser)
- PDF, DOCX, TXT 파일 지원
- 자동 정보 추출: 이메일, 전화번호, 기술 스택, 경력
"""

import re
from typing import Dict, List, Any, Optional
import os

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyPDF2가 설치되지 않았습니다. PDF 파싱을 사용하려면: pip install PyPDF2")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ python-docx가 설치되지 않았습니다. DOCX 파싱을 사용하려면: pip install python-docx")


class ResumeParser:
    """이력서 파싱 및 정보 추출"""

    # 한국 IT 업계에서 자주 사용되는 기술 키워드
    TECH_KEYWORDS = [
        # 프로그래밍 언어
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
        'Kotlin', 'Swift', 'PHP', 'Ruby', 'Scala',

        # 웹 프레임워크
        'React', 'Vue', 'Angular', 'Next.js', 'Nuxt.js',
        'Django', 'FastAPI', 'Flask', 'Spring', 'Express',

        # 데이터베이스
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Oracle',
        'MariaDB', 'Elasticsearch', 'DynamoDB',

        # 클라우드 & 인프라
        'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes', 'Jenkins',
        'Terraform', 'Ansible', 'CI/CD', 'GitHub Actions',

        # 기타
        'Git', 'Linux', 'Nginx', 'Apache', 'GraphQL', 'REST API',
        'Microservices', 'gRPC', 'Kafka', 'RabbitMQ'
    ]

    def __init__(self):
        self.tech_keywords = self.TECH_KEYWORDS

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2가 설치되지 않았습니다. pip install PyPDF2")

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def extract_text_from_docx(self, docx_path: str) -> str:
        """DOCX에서 텍스트 추출"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx가 설치되지 않았습니다. pip install python-docx")

        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def extract_text_from_txt(self, txt_path: str) -> str:
        """TXT에서 텍스트 추출"""
        encodings = ['utf-8', 'cp949', 'euc-kr']

        for encoding in encodings:
            try:
                with open(txt_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise ValueError(f"텍스트 파일을 읽을 수 없습니다: {txt_path}")

    def extract_email(self, text: str) -> Optional[str]:
        """이메일 추출"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else None

    def extract_phone(self, text: str) -> Optional[str]:
        """전화번호 추출 (한국 형식)"""
        # 010-1234-5678, 02-123-4567, 031-123-4567 등
        phone_patterns = [
            r'01[0-9]-\d{3,4}-\d{4}',  # 휴대폰
            r'0\d{1,2}-\d{3,4}-\d{4}',  # 일반 전화
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return phones[0]

        return None

    def extract_name(self, text: str) -> Optional[str]:
        """이름 추출 (간단한 휴리스틱)"""
        # "이름:", "성명:" 등의 패턴 찾기
        name_patterns = [
            r'이름\s*[:：]\s*([가-힣]{2,4})',
            r'성명\s*[:：]\s*([가-힣]{2,4})',
            r'Name\s*[:：]\s*([A-Za-z\s]{2,20})',
        ]

        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        # 첫 줄에서 한글 이름 찾기 (2-4글자)
        first_lines = text.split('\n')[:5]
        for line in first_lines:
            line = line.strip()
            if re.match(r'^[가-힣]{2,4}$', line):
                return line

        return None

    def extract_skills(self, text: str) -> List[str]:
        """기술 스택 추출"""
        found_skills = []
        text_lower = text.lower()

        for tech in self.tech_keywords:
            # 대소문자 무시하고 검색
            if tech.lower() in text_lower:
                if tech not in found_skills:
                    found_skills.append(tech)

        return sorted(found_skills)

    def extract_experience_years(self, text: str) -> int:
        """경력 연수 추출"""
        # "3년", "5년 경력", "경력 2년" 등의 패턴
        patterns = [
            r'경력\s*[:：]?\s*(\d+)\s*년',
            r'(\d+)\s*년\s*경력',
            r'(\d+)\s*년\s*차',
        ]

        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            years.extend([int(y) for y in matches])

        # 가장 큰 값 반환 (여러 개 있을 경우)
        return max(years) if years else 0

    def extract_education(self, text: str) -> List[str]:
        """학력 추출"""
        education_keywords = ['대학교', '대학원', '학사', '석사', '박사']
        education = []

        lines = text.split('\n')
        for line in lines:
            for keyword in education_keywords:
                if keyword in line:
                    education.append(line.strip())
                    break

        return education

    def extract_projects(self, text: str) -> List[str]:
        """프로젝트 경험 추출 (간단한 버전)"""
        project_keywords = ['프로젝트', 'project', '개발', '구축']
        projects = []

        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in project_keywords:
                if keyword in line_lower and len(line.strip()) > 10:
                    # 프로젝트 관련 줄과 다음 2줄 포함
                    project_text = line.strip()
                    if i + 1 < len(lines):
                        project_text += " " + lines[i + 1].strip()

                    if project_text not in projects:
                        projects.append(project_text)
                    break

        return projects[:5]  # 최대 5개

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """이력서 파일 파싱 (메인 함수)"""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 1. 파일 형식에 따라 텍스트 추출
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            text = self.extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")

        # 2. 정보 추출
        result = {
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'skills': self.extract_skills(text),
            'experience_years': self.extract_experience_years(text),
            'education': self.extract_education(text),
            'projects': self.extract_projects(text),
            'raw_text': text,
            'file_path': file_path
        }

        return result


# ==================== 사용 예시 ====================

def create_sample_resume():
    """테스트용 샘플 이력서 생성"""
    sample_text = """
이름: 김개발
이메일: kim.dev@example.com
전화번호: 010-1234-5678

[경력]
총 경력: 3년

[기술 스택]
- 백엔드: Python, FastAPI, Django, PostgreSQL, Redis
- 프론트엔드: React, TypeScript, Next.js
- 인프라: Docker, Kubernetes, AWS, CI/CD
- 기타: Git, Linux, REST API, GraphQL

[학력]
- 서울대학교 컴퓨터공학과 학사 (2018-2022)

[프로젝트 경험]
1. 전자상거래 플랫폼 개발 (2022-2023)
   - FastAPI를 사용한 REST API 서버 개발
   - PostgreSQL 데이터베이스 설계 및 최적화
   - Docker를 활용한 컨테이너화

2. 마이크로서비스 아키텍처 구축 (2023-2024)
   - Kubernetes 기반 서비스 오케스트레이션
   - gRPC를 활용한 서비스 간 통신
   - AWS EKS 배포 및 운영

3. 실시간 채팅 시스템 개발 (2024-현재)
   - WebSocket을 활용한 실시간 통신
   - Redis Pub/Sub 메시징
   - React 기반 프론트엔드 개발
"""

    # 샘플 파일 저장
    sample_file = "sample_resume.txt"
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_text)

    return sample_file


if __name__ == "__main__":
    print("🚀 이력서 파서 테스트")
    print("=" * 60)

    # 1. 샘플 이력서 생성
    print("\n📄 샘플 이력서 생성 중...")
    sample_file = create_sample_resume()
    print(f"✅ 생성 완료: {sample_file}")

    # 2. 이력서 파싱
    print("\n🔍 이력서 파싱 중...")
    parser = ResumeParser()

    try:
        result = parser.parse_resume(sample_file)

        print("\n✅ 파싱 완료!")
        print("\n" + "=" * 60)
        print("📊 추출된 정보")
        print("=" * 60)

        print(f"\n👤 이름: {result['name']}")
        print(f"📧 이메일: {result['email']}")
        print(f"📱 전화번호: {result['phone']}")
        print(f"💼 경력: {result['experience_years']}년")

        print(f"\n🛠️ 기술 스택 ({len(result['skills'])}개):")
        for skill in result['skills']:
            print(f"   - {skill}")

        print(f"\n🎓 학력 ({len(result['education'])}개):")
        for edu in result['education']:
            print(f"   - {edu}")

        print(f"\n💡 프로젝트 ({len(result['projects'])}개):")
        for i, project in enumerate(result['projects'], 1):
            print(f"   {i}. {project[:80]}...")

        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 샘플 파일 삭제
        if os.path.exists(sample_file):
            os.remove(sample_file)
            print(f"\n🗑️ 샘플 파일 삭제: {sample_file}")
