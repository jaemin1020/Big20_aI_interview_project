import torch
from transformers import AutoTokenizer, AutoModel
import json
import numpy as np
import os

MODEL_NAME = "nlpai-lab/KURE-v1"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =========================
# 모델 로드 (자동 다운로드)
# =========================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
model.eval()

# =========================
# Mean Pooling
# =========================
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, dim=1) / torch.clamp(
        input_mask_expanded.sum(dim=1), min=1e-9
    )

# =========================
# 임베딩 함수
# =========================
def embed_text(text: str) -> list:
    if not text or not text.strip():
        return None

    encoded_input = tokenizer(
        text,
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=1024
    )

    encoded_input = {k: v.to(DEVICE) for k, v in encoded_input.items()}

    with torch.no_grad():
        model_output = model(**encoded_input)

    embedding = mean_pooling(model_output, encoded_input["attention_mask"])
    embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

    return embedding.cpu().numpy()[0].tolist()

# =========================
# 직렬화 함수 (Text Serialization)
# =========================
def serialize_profile(profile):
    return f"이름: {profile.get('name','')}\n지원직무: {profile.get('target_position','')}\n지원회사: {profile.get('target_company','')}".strip()

def serialize_experience(exp):
    return f"회사: {exp.get('company','')}\n역할: {exp.get('role','')}\n내용: {exp.get('description','')}".strip()

def serialize_project(proj):
    return f"프로젝트명: {proj.get('title','')}\n내용: {proj.get('description','')}".strip()

# =========================
# 메인 임베딩 파이프라인 (수정됨)
# =========================
def build_resume_embeddings(resume_json: dict):
    # 최상단 구조에 target_company 추가
    # resume_json["profile"] 내에 해당 정보가 있다고 가정합니다.
    output = {
        "resume_id": resume_json.get("resume_id", "res_001"),
        "name": resume_json["profile"].get("name", ""),
        "role": resume_json["profile"].get("target_position", ""),
        "target_company": resume_json["profile"].get("target_company", ""), # 필수 추가 필드
        "embeddings": {
            "profile": {},
            "experience": [],
            "projects": [],
            "self_introduction": [],
            "certifications": {},
            "languages": {}
        }
    }

    print(f"[*] 분석 대상: {output['name']} / 지원회사: {output['target_company']}")

    # -------- profile --------
    profile_text = serialize_profile(resume_json["profile"])
    output["embeddings"]["profile"]["vector"] = embed_text(profile_text)

    # -------- experience --------
    for idx, exp in enumerate(resume_json.get("experience", []), start=1):
        text = serialize_experience(exp)
        output["embeddings"]["experience"].append({
            "id": f"exp_{idx}",
            "vector": embed_text(text)
        })

    # -------- projects --------
    for idx, proj in enumerate(resume_json.get("projects", []), start=1):
        text = serialize_project(proj)
        output["embeddings"]["projects"].append({
            "id": f"proj_{idx}",
            "vector": embed_text(text)
        })

    # -------- self introduction --------
    for si in resume_json.get("self_introduction", []):
        si_text = f"질문: {si.get('question','')}\n답변: {si.get('answer','')}".strip()
        q = si.get("question","")

        # 분류 로직 (필요 시 수정)
        if "지원한 이유" in q or "동기" in q: si_type = "지원동기"
        elif "협업" in q: si_type = "협업경험"
        else: si_type = "일반"

        output["embeddings"]["self_introduction"].append({
            "type": si_type,
            "vector": embed_text(si_text)
        })

    return output

# =========================
# 실행부
# =========================
if __name__ == "__main__":
    input_file = "resume_structured.json"
    
    if os.path.exists(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            resume_data = json.load(f)

        print("[*] 멀티 섹션 임베딩 생성 중...")
        embedding_result = build_resume_embeddings(resume_data)

        output_file = "resume_multi_embeddings.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(embedding_result, f, indent=2, ensure_ascii=False)

        print(f"\n[완료] {output_file} 생성됨.")
        print(f"매칭 대상 회사: {embedding_result['target_company']}")
    else:
        print(f"파일을 찾을 수 없습니다: {input_file}")