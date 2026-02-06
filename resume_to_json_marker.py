import os
import json
import gc
from typing import List
import torch
import ollama
from pydantic import BaseModel, Field

# Marker 라이브러리 (이력서 PDF 파싱용)
try:
    from marker.convert import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
except ImportError:
    print("[!] 'marker-pdf' 라이브러리가 설치되어 있지 않습니다. (pip install marker-pdf)")
    PdfConverter = None

class SelfIntroSchema(BaseModel):
    growth: str = Field(description="성장과정 섹션의 전체 원문 (절대 요약 금지)")
    personality: str = Field(description="성격의 장단점 섹션의 전체 원문 (절대 요약 금지)")
    motivation: str = Field(description="지원동기 섹션의 전체 원문 (절대 요약 금지)")
    aspiration: str = Field(description="입사 후 포부 섹션의 전체 원문 (절대 요약 금지)")

class ResumeSchema(BaseModel):
    name: str = Field(description="이름")
    target_company: str = Field(description="지원 회사명")
    target_position: str = Field(description="지원 직무명")
    education: List[dict] = Field(description="학교명, 전공, 기간 리스트 (예: [{'school': 'OO대학교', 'major': '컴퓨터공학', 'period': '2015-2019'}])")
    certifications: List[str] = Field(description="자격증 리스트")
    technical_skills: List[str] = Field(description="기술 스택 리스트")
    experience: List[dict] = Field(description="경력 사항 리스트 (예: [{'company': 'OO사', 'position': '사원', 'period': '2020-2022', 'description': '...' }])")
    projects: List[dict] = Field(description="프로젝트 리스트 (예: [{'name': '프로젝트A', 'period': '2021', 'description': '...', 'tech_stack': ['Python', 'SQL']}])")
    self_intro: SelfIntroSchema = Field(description="자기소개서 각 항목의 토씨 하나 틀리지 않은 원문")

def process_resume_with_marker(pdf_path: str):
    """
    Marker를 사용하여 PDF를 마크다운으로 변환한 후 EXAONE으로 JSON 구조화합니다.
    """
    if not os.path.exists(pdf_path):
        print(f"[!] 파일을 찾을 수 없습니다: {pdf_path}")
        return None

    # --- STEP 1: Marker 파싱 (Markdown 변환) ---
    print(f"[*] Marker 파싱 시작: {pdf_path}")
    
    if PdfConverter is None:
        print("[!] Marker 라이브러리가 없어 파싱을 진행할 수 없습니다.")
        return None

    try:
        artifact_dict = create_model_dict()
        converter = PdfConverter(artifact_dict=artifact_dict)
        
        rendered = converter(pdf_path)
        full_markdown, _, _ = text_from_rendered(rendered)
        
        # 메모리 관리
        del converter
        del artifact_dict
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    except Exception as e:
        print(f"[!] Marker 파싱 중 오류 발생: {e}")
        return None

    # --- STEP 2: EXAONE 3.5 (latest)로 정보 추출 ---
    print("[*] EXAONE 3.5 데이터 구조화 시작...")
    
    # 요청하신 system_msg 적용
    system_msg = (
        "당신은 이력서 데이터를 정확하게 구조화하는 전문가입니다. "
        "특히 'self_intro' 섹션은 입력된 텍스트의 내용을 절대로 요약하거나 수정하지 말고, "
        "문장 그대로를 복사하여 JSON 값을 채워야 합니다. 원문 유지 유무가 당신의 성능 평가 척도입니다."
    )
    
    # 요청하신 prompt 적용
    prompt = f"""
    아래 이력서 텍스트에서 정보를 추출하여 JSON으로 출력해줘.

    [제약 사항]
    1. self_intro의 모든 항목(성장과정, 성격, 지원동기, 포부)은 원문을 토씨 하나 틀리지 않고 그대로 가져올 것.
    2. 데이터가 없는 항목은 빈 리스트([])나 빈 문자열("")로 처리할 것.
    3. 반드시 JSON 형식으로만 응답할 것.

    [이력서 텍스트]
    {full_markdown}
    
    [응답 JSON 스키마]
    {json.dumps(ResumeSchema.model_json_schema(), ensure_ascii=False)}
    """

    try:
        response = ollama.generate(
            model="exaone3.5:latest", # 현재 설치된 latest 사용 (필요시 2.4b 로 변경 가능)
            system=system_msg,
            prompt=prompt,
            format="json",
            options={
                "temperature": 0,
                "num_predict": 4096,
                "top_p": 0.1
            }
        )
        
        return json.loads(response['response'])
        
    except Exception as e:
        print(f"[!] Ollama 처리 또는 JSON 파싱 오류: {e}")
        return None

if __name__ == "__main__":
    target_file = r"C:\lyn\llm_test\AI 이력서(1) 최승우_수정.pdf"
    
    final_json = process_resume_with_marker(target_file)
    
    if final_json:
        print("\n[추출 완료된 JSON 데이터]")
        print(json.dumps(final_json, indent=2, ensure_ascii=False))
    else:
        print("\n[!] 데이터 추출에 실패했습니다.")
