import os
import json
import gc
from typing import List
import torch
import ollama
from pydantic import BaseModel, Field

# 사용자님 컴퓨터에 설치된 marker-pdf 버전에 맞춘 경로
from marker.converters.pdf import PdfConverter  # 이 부분이 핵심입니다!
from marker.models import create_model_dict
from marker.output import text_from_rendered


# 1. 라이브러리 로드 부분 수정
try:
    # 사용자님의 환경에 맞는 경로로 수정
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    print("[*] Marker 라이브러리 로드 성공!")
    MARKER_AVAILABLE = True
except ImportError:
    try:
        # 혹시 다른 버전일 경우를 대비한 구 버전 경로
        from marker.convert import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
        print("[*] Marker 라이브러리 로드 성공! (Alternative Path)")
        MARKER_AVAILABLE = True
    except ImportError:
        print("[!] Marker 로드 실패. PyMuPDF로 전환 준비 중...")
        MARKER_AVAILABLE = False

try:
    import fitz  # PyMuPDF (백업용)
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# --- Schema 정의 (기존과 동일) ---
class SelfIntroSchema(BaseModel):
    growth: str = Field(description="성장과정 섹션 원문")
    personality: str = Field(description="성격의 장단점 섹션 원문")
    motivation: str = Field(description="지원동기 섹션 원문")
    aspiration: str = Field(description="입사 후 포부 섹션 원문")

class ResumeSchema(BaseModel):
    name: str = Field(description="이름")
    target_company: str = Field(description="지원 회사명")
    target_position: str = Field(description="지원 직무명")
    education: List[dict] = Field(description="학력 리스트")
    certifications: List[str] = Field(description="자격증 리스트")
    technical_skills: List[str] = Field(description="기술 스택 리스트")
    experience: List[dict] = Field(description="경력 리스트")
    projects: List[dict] = Field(description="프로젝트 리스트")
    self_intro: SelfIntroSchema = Field(description="자기소개서 원문")

def extract_text(pdf_path: str):
    """Marker 우선 시도, 실패 시 PyMuPDF 사용"""
    if MARKER_AVAILABLE:
        try:
            print(f"[*] Marker 파싱 시작...")
            artifact_dict = create_model_dict()
            converter = PdfConverter(artifact_dict=artifact_dict)
            rendered = converter(pdf_path)
            full_markdown, _, _ = text_from_rendered(rendered)
            
            del converter
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            return full_markdown
        except Exception as e:
            print(f"[!] Marker 실행 중 에러 발생: {e}. 백업 모드로 전환합니다.")

    if PYMUPDF_AVAILABLE:
        print(f"[*] PyMuPDF(fitz) 백업 모드 가동...")
        doc = fitz.open(pdf_path)
        text = "".join([page.get_text() for page in doc])
        return text
    
    return None

def process_resume_to_json(pdf_path: str):
    full_content = extract_text(pdf_path)
    if not full_content:
        print("[!] 텍스트 추출에 실패했습니다.")
        return None

    print("[*] EXAONE 3.5 데이터 구조화 시작...")
    # 1. 시스템 메시지: 모델의 역할과 절대 금기 사항 설정
    system_msg = (
        "당신은 이력서 및 자기소개서 데이터 구조화 전문 AI입니다. "
        "당신의 가장 중요한 임무는 '원문 보존'입니다. "
        "특히 'self_intro'(자기소개서)의 각 항목을 추출할 때, 텍스트를 요약하거나, "
        "말투를 수정하거나, 문장 구조를 변경하는 행위를 절대 금지합니다. "
        "토씨 하나 틀리지 않고 입력된 원문 그대로를 복사하여 값을 채우는 것이 당신의 성능 평가 기준입니다."
    )

    # 2. 프롬프트: 구체적인 추출 지시 및 제약 사항
    prompt = f"""
아래의 [이력서 원문]에서 정보를 추출하여 [JSON 스키마] 형식에 맞춰 응답하십시오.

### [추출 규칙]
1. **자기소개서(self_intro) 무결성**: 
   - 성장과정, 성격, 지원동기, 포부 항목은 반드시 원본 텍스트를 그대로 가져오십시오.
   - **절대 요약 금지**, **단어 수정 금지**, **문장 생략 금지**. 
   - 줄바꿈(\n)이 있다면 이를 포함하여 텍스트 전체를 값으로 입력하십시오.
2. **누락된 정보**: 
   - 원문에 해당 정보가 명시되지 않은 경우, 빈 리스트([]) 또는 빈 문자열("")로 처리하십시오.
3. **직무 및 회사**: 
   - "target_company"(안랩)와 "target_position"(보안엔지니어) 정보를 정확히 매칭하십시오.
4. **출력 형식**: 
   - 오직 JSON 데이터만 출력하고, 다른 설명이나 인사는 생략하십시오.

### [JSON 스키마]
{json.dumps(ResumeSchema.model_json_schema(), ensure_ascii=False)}

### [이력서 원문]
{full_content}
"""

    try:
        response = ollama.generate(
            model="exaone3.5:latest",
            system=system_msg,
            prompt=prompt,
            format="json",
            options={"temperature": 0, "num_predict": 4096}
        )
        return json.loads(response['response'])
    except Exception as e:
        print(f"[!] Ollama 처리 오류: {e}")
        return None

if __name__ == "__main__":
    target_file = r"C:\big20\Big20_aI_interview_project\AI 이력서(1) 최승우_수정.pdf"
    
    if os.path.exists(target_file):
        final_json = process_resume_to_json(target_file)
        if final_json:
            print("\n[추출 완료된 JSON 데이터]")
            print(json.dumps(final_json, indent=2, ensure_ascii=False))
            # 결과 저장
            with open("resume_result.json", "w", encoding="utf-8") as f:
                json.dump(final_json, f, indent=2, ensure_ascii=False)
    else:
        print(f"[!] 파일을 찾을 수 없습니다: {target_file}")


      "position": "인턴",
      "period": "2023 년 7 월 - 2023 년 8 월",
      "description": "공공기관 보안 관제 시스템 모니터링 보조 및 일일 위협 분석 보고서 작성  
지원 업무 수행, 보안 취약점 점검 스크립트 기초 설계 참여"
    }
  ],
  "projects": [
    {
      "title": "오픈소스 기반 침입 탐지 시스템(IDS) 구축 프로젝트",
      "period": "2024.03 – 2024.06",
      "description": "학내 가상 네트워크망 보안 강화를 위한 환경 구축 및 탐지 규칙 설계 주도, Snort 활용한 실시간 패킷 수집 환경 조성 및 SQL 인젝션, DDoS 공격 식별 성과 달성, 로그 분석  
자동화 툴과 시각화 대시보드 연동 설계"
    }
  ],
      "position": "인턴",
      "period": "2023 년 7 월 - 2023 년 8 월",
      "description": "공공기관 보안 관제 시스템 모니터링 보조 및 일일 위협 분석 보고서 작성  
지원 업무 수행, 보안 취약점 점검 스크립트 기초 설계 참여"
    }
  ],
  "projects": [
    {
      "title": "오픈소스 기반 침입 탐지 시스템(IDS) 구축 프로젝트",
      "period": "2024.03 – 2024.06",
      "description": "학내 가상 네트워크망 보안 강화를 위한 환경 구축 및 탐지 규칙 설계 주도, Snort 활용한 실시간 패킷 수집 환경 조성 및 SQL 인젝션, DDoS 공격 식별 성과 달성, 로그 분석  
자동화 툴과 시각화 대시보드 연동 설계"
    }
  ],
  "projects": [
    {
      "title": "오픈소스 기반 침입 탐지 시스템(IDS) 구축 프로젝트",
      "period": "2024.03 – 2024.06",
      "description": "학내 가상 네트워크망 보안 강화를 위한 환경 구축 및 탐지 규칙 설계 주도, Snort 활용한 실시간 패킷 수집 환경 조성 및 SQL 인젝션, DDoS 공격 식별 성과 달성, 로그 분석  
자동화 툴과 시각화 대시보드 연동 설계"
    }
  ],
  "self_intro": {
    "growth": "중학생 시절 지인의 개인정보 유출 피해를 목격하며 보안의 중요성을 깨닫고 정보보
호학을 전공하며 전문성을 쌓아왔습니다. 다양한 경험을 통해 실무적인 방어 기제와 기술적 문제 해
결 능력을 키워왔습니다.\n\n",
      "description": "학내 가상 네트워크망 보안 강화를 위한 환경 구축 및 탐지 규칙 설계 주도, Snort 활용한 실시간 패킷 수집 환경 조성 및 SQL 인젝션, DDoS 공격 식별 성과 달성, 로그 분석  
자동화 툴과 시각화 대시보드 연동 설계"
    }
  ],
  "self_intro": {
    "growth": "중학생 시절 지인의 개인정보 유출 피해를 목격하며 보안의 중요성을 깨닫고 정보보
호학을 전공하며 전문성을 쌓아왔습니다. 다양한 경험을 통해 실무적인 방어 기제와 기술적 문제 해
결 능력을 키워왔습니다.\n\n",
    "personality": "꼼꼼하고 분석적인 성격으로, 팀원 간의 투명한 정보 공유와 협력을 중요시하 
며, 새로운 기술 도입 시 능동적인 학습 태도를 갖추고 있습니다.\n\n",
    "motivation": "안랩은 대한민국 보안의 선두주자로서, 제 윤리 의식과 사명감을 가장 잘 실현 
할 수 있는 환경을 제공합니다. 사회 안전망 구축에 기여하고자 지원했습니다.\n\n",
    "aspiration": "입사 초기에는 실시간 모니터링 업무에서 무결점 탐지율을 유지하고, 3년 내에 
  "self_intro": {
    "growth": "중학생 시절 지인의 개인정보 유출 피해를 목격하며 보안의 중요성을 깨닫고 정보보
호학을 전공하며 전문성을 쌓아왔습니다. 다양한 경험을 통해 실무적인 방어 기제와 기술적 문제 해
결 능력을 키워왔습니다.\n\n",
    "personality": "꼼꼼하고 분석적인 성격으로, 팀원 간의 투명한 정보 공유와 협력을 중요시하 
며, 새로운 기술 도입 시 능동적인 학습 태도를 갖추고 있습니다.\n\n",
    "motivation": "안랩은 대한민국 보안의 선두주자로서, 제 윤리 의식과 사명감을 가장 잘 실현 
할 수 있는 환경을 제공합니다. 사회 안전망 구축에 기여하고자 지원했습니다.\n\n",
    "aspiration": "입사 초기에는 실시간 모니터링 업무에서 무결점 탐지율을 유지하고, 3년 내에 
    "personality": "꼼꼼하고 분석적인 성격으로, 팀원 간의 투명한 정보 공유와 협력을 중요시하 
며, 새로운 기술 도입 시 능동적인 학습 태도를 갖추고 있습니다.\n\n",
    "motivation": "안랩은 대한민국 보안의 선두주자로서, 제 윤리 의식과 사명감을 가장 잘 실현 
할 수 있는 환경을 제공합니다. 사회 안전망 구축에 기여하고자 지원했습니다.\n\n",
    "aspiration": "입사 초기에는 실시간 모니터링 업무에서 무결점 탐지율을 유지하고, 3년 내에 
는 머신러닝 기술을 활용한 지능형 위험 탐지 시스템을 주도적으로 구축하겠습니다. 궁극적으로는  
할 수 있는 환경을 제공합니다. 사회 안전망 구축에 기여하고자 지원했습니다.\n\n",
    "aspiration": "입사 초기에는 실시간 모니터링 업무에서 무결점 탐지율을 유지하고, 3년 내에 
는 머신러닝 기술을 활용한 지능형 위험 탐지 시스템을 주도적으로 구축하겠습니다. 궁극적으로는  
는 머신러닝 기술을 활용한 지능형 위험 탐지 시스템을 주도적으로 구축하겠습니다. 궁극적으로는  
글로벌 위협 트렌드에 선제적으로 대응할 수 있는 보   아키텍처 전문가로 성장하여 안랩의 글로벌 
안 아키텍처 전문가로 성장하여 안랩의 글로벌 경쟁력
 강화에 기여하겠습니다.\n\n"
  }
}
