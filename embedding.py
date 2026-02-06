import torch
from transformers import AutoTokenizer, AutoModel
import json
import numpy as np

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
# 직렬화 함수
# =========================
def serialize_profile(profile):
    return f"""
이름: {profile.get('name','')}
지원직무: {profile.get('target_position','')}
지원회사: {profile.get('target_company','')}
연락처: {profile.get('contact','')}
""".strip()

def serialize_experience(exp):
    return f"""
회사: {exp.get('company','')}
지역: {exp.get('location','')}
직무: {exp.get('role','')}
기간: {exp.get('period','')}
내용: {exp.get('description','')}
""".strip()

def serialize_project(proj):
    return f"""
프로젝트명: {proj.get('title','')}
기간: {proj.get('period','')}
내용: {proj.get('description','')}
""".strip()

def serialize_certifications(certs):
    return "\n".join([f"{c.get('name','')} {c.get('date','')}" for c in certs])

def serialize_languages(langs):
    return "\n".join([f"{l.get('name','')} {l.get('date','')}" for l in langs])

# =========================
# 메인 임베딩 파이프라인
# =========================
def build_resume_embeddings(resume_json: dict):

    output = {
        "resume_id": resume_json.get("resume_id", "res_001"),
        "role": resume_json["profile"]["target_position"],
        "embeddings": {
            "profile": {},
            "experience": [],
            "projects": [],
            "self_introduction": [],
            "certifications": {},
            "languages": {}
        }
    }

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
        si_text = f"""
질문: {si.get('question','')}
답변: {si.get('answer','')}
""".strip()

        q = si.get("question","")

        # 질문 타입 자동 분류 (룰 기반)
        if "지원한 이유" in q or "성장계획" in q:
            si_type = "지원동기/성장계획"
        elif "협업" in q:
            si_type = "협업경험"
        elif "연구" in q or "프로젝트" in q:
            si_type = "연구/프로젝트"
        elif "학습" in q or "노하우" in q:
            si_type = "학습노하우"
        else:
            si_type = "기타"

        output["embeddings"]["self_introduction"].append({
            "type": si_type,
            "vector": embed_text(si_text)
        })

    # -------- certifications --------
    cert_text = serialize_certifications(resume_json.get("certifications", []))
    output["embeddings"]["certifications"]["vector"] = embed_text(cert_text)

    # -------- languages --------
    lang_text = serialize_languages(resume_json.get("languages", []))
    output["embeddings"]["languages"]["vector"] = embed_text(lang_text)

    return output

# =========================
# 실행부
# =========================
if __name__ == "__main__":

    with open("resume_structured.json", "r", encoding="utf-8") as f:
        resume_json = json.load(f)

    print("[*] 멀티 섹션 임베딩 생성 중...")
    embedding_result = build_resume_embeddings(resume_json)

    with open("resume_multi_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(embedding_result, f, indent=2, ensure_ascii=False)

    print("\n[완료]")
    print("→ resume_multi_embeddings.json 생성")
    print("→ 멀티 벡터 RAG 구조 완성")
