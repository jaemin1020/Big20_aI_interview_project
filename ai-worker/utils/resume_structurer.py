"""
실제 AI 이력서 구조 기반 파서 (개선 버전)
"""
import logging
import json
import re
from typing import Dict, List, Optional

logger = logging.getLogger("ResumeStructurer")


class ResumeStructurer:
    """실제 이력서 구조 기반 파서"""
    
    @staticmethod
    def structure_resume(text: str) -> Dict:
        """
        실제 이력서 구조에 맞춰 파싱
        
        Args:
            text: 이력서 텍스트
            
        Returns:
            dict: 구조화된 이력서 데이터
        """
        structured = {
            "personal_info": ResumeStructurer._extract_personal_info(text),
            "target_position": ResumeStructurer._extract_target_position(text),
            "experience": ResumeStructurer._extract_experience(text),
            "education": ResumeStructurer._extract_education(text),
            "certifications": ResumeStructurer._extract_certifications(text),
            "projects": ResumeStructurer._extract_projects(text),
            "skills": ResumeStructurer._extract_skills(text),
            "languages": ResumeStructurer._extract_languages(text),
            "cover_letter": ResumeStructurer._extract_cover_letter(text)
        }
        
        return structured
    
    @staticmethod
    def _extract_personal_info(text: str) -> Dict:
        """개인 정보 추출"""
        info = {}
        
        # 이름 (첫 줄에서 한글 이름 찾기)
        name_match = re.search(r'^([가-힣]{2,4})\s*$', text, re.MULTILINE)
        if name_match:
            info["name"] = name_match.group(1)
        
        # 주소
        address_match = re.search(r'((?:서울|경기도|부산|대구|인천|광주|대전|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주)[^\n]+)', text)
        if address_match:
            info["address"] = address_match.group(1).strip()
        
        # 전화번호
        phone_match = re.search(r'\(\+82\)\s*([\d\-]+)', text)
        if phone_match:
            info["phone"] = f"+82 {phone_match.group(1)}"
        
        # 이메일
        email_match = re.search(r'([\w\.\-]+@[\w\.\-]+\.\w+)', text)
        if email_match:
            info["email"] = email_match.group(1)
        
        return info
    
    @staticmethod
    def _extract_target_position(text: str) -> Dict:
        """지원 직무 및 회사 추출"""
        target = {}
        
        # 지원 직무
        position_match = re.search(r'지원\s*직무\s*[:：]\s*(.+?)(?:\n|$)', text)
        if position_match:
            target["position"] = position_match.group(1).strip()
        
        # 지원 회사
        company_match = re.search(r'지원\s*회사\s*[:：]\s*(.+?)(?:\n|$)', text)
        if company_match:
            target["company"] = company_match.group(1).strip()
        
        return target
    
    @staticmethod
    def _extract_experience(text: str) -> List[Dict]:
        """경력 추출"""
        experiences = []
        
        # "경력" 섹션 찾기
        exp_section = re.search(
            r'경력\s*\n(.+?)(?:\n학력|\n자격증|\n프로젝트|$)',
            text,
            re.DOTALL
        )
        
        if exp_section:
            exp_text = exp_section.group(1)
            
            # 회사명 및 직책 패턴
            # 예: "한국인터넷진흥원(KISA), 서울 — 인턴"
            company_pattern = r'([가-힣()A-Za-z\s]+),\s*([가-힣]+)\s*—\s*(.+?)(?:\n|$)'
            companies = re.findall(company_pattern, exp_text)
            
            for company, location, position in companies:
                # 기간 찾기
                period_match = re.search(r'(\d{4}년\s*\d{1,2}월)\s*-\s*(\d{4}년\s*\d{1,2}월)', exp_text)
                period = f"{period_match.group(1)} ~ {period_match.group(2)}" if period_match else "N/A"
                
                # 업무 내용 추출 (다음 줄들)
                description_lines = []
                lines = exp_text.split('\n')
                in_description = False
                
                for line in lines:
                    line = line.strip()
                    if company.strip() in line:
                        in_description = True
                        continue
                    if in_description and line and not re.match(r'^\d{4}년', line):
                        if re.match(r'^[가-힣()A-Za-z\s]+,', line):  # 다음 회사 시작
                            break
                        description_lines.append(line)
                
                description = ' '.join(description_lines[:3])  # 최대 3줄
                
                experiences.append({
                    "company": company.strip(),
                    "location": location.strip(),
                    "position": position.strip(),
                    "duration": period,
                    "description": description,
                    "achievements": [],
                    "tech_stack": ResumeStructurer._extract_tech_from_text(description)
                })
        
        return experiences
    
    @staticmethod
    def _extract_education(text: str) -> List[Dict]:
        """학력 추출"""
        education = []
        
        # "학력" 섹션 찾기
        edu_section = re.search(
            r'학력\s*\n(.+?)(?:\n자격증|\n프로젝트|\n언어능력|$)',
            text,
            re.DOTALL
        )
        
        if edu_section:
            edu_text = edu_section.group(1)
            
            # 대학교 패턴
            # 예: "세종대학교 — 정보보호학 학사"
            univ_pattern = r'([가-힣]+대학교)\s*—\s*(.+?)\s*(학사|석사|박사)'
            universities = re.findall(univ_pattern, edu_text)
            
            for school, major, degree in universities:
                # 기간 찾기
                period_match = re.search(r'(\d{4})년\s*\d{1,2}월\s*-\s*(\d{4})년\s*\d{1,2}월', edu_text)
                graduation = f"{period_match.group(2)}-02" if period_match else None
                
                education.append({
                    "school": school.strip(),
                    "degree": degree.strip(),
                    "major": major.strip(),
                    "graduation_date": graduation,
                    "gpa": None
                })
            
            # 고등학교 패턴
            hs_pattern = r'([가-힣]+고등학교)\s*—\s*(.+)'
            high_schools = re.findall(hs_pattern, edu_text)
            
            for school, type_info in high_schools:
                education.append({
                    "school": school.strip(),
                    "degree": "고등학교 졸업",
                    "major": type_info.strip(),
                    "graduation_date": None,
                    "gpa": None
                })
        
        return education
    
    @staticmethod
    def _extract_certifications(text: str) -> List[Dict]:
        """자격증 추출"""
        certifications = []
        
        # "자격증" 섹션 찾기
        cert_section = re.search(
            r'자격증\s*\n(.+?)(?:\n프로젝트|\n언어능력|\n자기소개서|$)',
            text,
            re.DOTALL
        )
        
        if cert_section:
            cert_text = cert_section.group(1)
            
            # 자격증명 패턴 (쉼표로 구분)
            cert_names = re.findall(r'([가-힣A-Za-z0-9\s]+(?:기사|사|급|자격증))', cert_text)
            
            for name in cert_names:
                name = name.strip().rstrip(',')
                if name:
                    certifications.append({
                        "name": name,
                        "issuer": None,
                        "date": None
                    })
        
        return certifications
    
    @staticmethod
    def _extract_projects(text: str) -> List[Dict]:
        """프로젝트 추출"""
        projects = []
        
        # "프로젝트" 섹션 찾기
        proj_section = re.search(
            r'프로젝트\s*\n(.+?)(?:\n언어능력|\n자기소개서|$)',
            text,
            re.DOTALL
        )
        
        if proj_section:
            proj_text = proj_section.group(1)
            
            # 프로젝트명 (첫 줄)
            lines = [line.strip() for line in proj_text.split('\n') if line.strip()]
            
            if lines:
                project_name = lines[0]
                description = ' '.join(lines[1:]) if len(lines) > 1 else ""
                
                projects.append({
                    "name": project_name,
                    "duration": None,
                    "description": description,
                    "role": None,
                    "tech_stack": ResumeStructurer._extract_tech_from_text(description),
                    "achievements": []
                })
        
        return projects
    
    @staticmethod
    def _extract_skills(text: str) -> Dict:
        """기술 스택 추출"""
        skills = {
            "security": [],
            "programming_languages": [],
            "frameworks": [],
            "databases": [],
            "devops": [],
            "tools": []
        }
        
        # 보안 기술 키워드
        security_keywords = ["Network 패킷 분석", "Wireshark", "리눅스 시스템 관리", 
                           "방화벽", "악성코드 분석", "IDS", "Snort", "침입 탐지"]
        
        for keyword in security_keywords:
            if keyword in text:
                skills["security"].append(keyword)
        
        # 프로그래밍 언어 (일반적인 키워드)
        lang_keywords = ["Python", "Java", "C++", "C#", "JavaScript"]
        for lang in lang_keywords:
            if re.search(r'\b' + re.escape(lang) + r'\b', text, re.IGNORECASE):
                skills["programming_languages"].append(lang)
        
        return skills
    
    @staticmethod
    def _extract_languages(text: str) -> List[Dict]:
        """언어 능력 추출"""
        languages = []
        
        # "언어능력" 섹션 찾기
        lang_section = re.search(
            r'언어능력\s*\n(.+?)(?:\n자기소개서|$)',
            text,
            re.DOTALL
        )
        
        if lang_section:
            lang_text = lang_section.group(1)
            
            # 영어 점수
            toeic_match = re.search(r'영어\(TOEIC\s*(\d+)점\)', lang_text)
            if toeic_match:
                languages.append({
                    "language": "영어",
                    "proficiency": f"TOEIC {toeic_match.group(1)}점"
                })
            
            # 일본어 점수
            jlpt_match = re.search(r'일본어\(JLPT\s*(N\d)\)', lang_text)
            if jlpt_match:
                languages.append({
                    "language": "일본어",
                    "proficiency": f"JLPT {jlpt_match.group(1)}"
                })
        
        return languages
    
    @staticmethod
    def _extract_cover_letter(text: str) -> Dict:
        """자기소개서 추출"""
        cover_letter = {}
        
        # "자기소개서" 섹션 찾기
        cl_section = re.search(
            r'자기소개서\s*\n(.+)$',
            text,
            re.DOTALL
        )
        
        if cl_section:
            cl_text = cl_section.group(1)
            
            # 성장과정
            growth_match = re.search(r'성장과정\s*\n(.+?)(?:\n성격의\s*장단점|\n지원동기|$)', cl_text, re.DOTALL)
            if growth_match:
                cover_letter["growth_process"] = growth_match.group(1).strip()
            
            # 성격의 장단점
            personality_match = re.search(r'성격의\s*장단점\s*\n(.+?)(?:\n지원동기|\n입사후포부|$)', cl_text, re.DOTALL)
            if personality_match:
                cover_letter["personality"] = personality_match.group(1).strip()
            
            # 지원동기
            motivation_match = re.search(r'지원동기\s*\n(.+?)(?:\n입사후포부|$)', cl_text, re.DOTALL)
            if motivation_match:
                cover_letter["motivation"] = motivation_match.group(1).strip()
            
            # 입사후포부
            aspiration_match = re.search(r'입사후포부\s*\n(.+)$', cl_text, re.DOTALL)
            if aspiration_match:
                cover_letter["aspiration"] = aspiration_match.group(1).strip()
        
        return cover_letter
    
    @staticmethod
    def _extract_tech_from_text(text: str) -> List[str]:
        """텍스트에서 기술 키워드 추출"""
        tech_keywords = [
            "Wireshark", "Snort", "IDS", "방화벽", "리눅스", "Linux",
            "Python", "Java", "C++", "머신러닝", "Machine Learning"
        ]
        
        found_tech = []
        for keyword in tech_keywords:
            if keyword in text:
                found_tech.append(keyword)
        
        return found_tech


# 사용 예시
if __name__ == "__main__":
    # 테스트용 이력서 텍스트
    with open("resume_text.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    
    structurer = ResumeStructurer()
    result = structurer.structure_resume(resume_text)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
