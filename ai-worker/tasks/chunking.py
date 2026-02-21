import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter # [문법] 긴 글을 똑똑하게 자르는 도구

def chunk_resume(parsed_data):
    """
    구조화된 이력서 데이터를 받아서 AI 검색용 조각(Chunk)들로 변환합니다.
    """
    chunks = []
    print("\n[STEP4] 데이터 청킹(Chunking) 시작...")

    # ====================================================
    # 1. 텍스트 분할기 설정 (Text Splitter)
    # [해석] 자소서 답변처럼 긴 글을 어떻게 자를지 정하는 '가이드라인'입니다.
    # ====================================================
    # [문법] RecursiveCharacterTextSplitter: 
    # chunk_size=600: 한 조각을 최대 600자로 맞춤
    # chunk_overlap=100: 조각끼리 100자 정도 겹치게 해서 앞뒤 문맥이 안 끊기게 함
    # separators: 자를 때 기준 (문단 -> 문장 -> 단어 순서로 시도)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    # ----------------------------------------------------
    # 2. 헤더 정보 (Profile)
    # ----------------------------------------------------
    header = parsed_data.get("header", {}) # [문법] .get("key", {}): 키가 없으면 빈 딕셔너리를 돌려줘서 에러를 방지함
    if header:
        name = header.get("name", "")
        role = header.get("target_role", "")
        company = header.get("target_company", "")
        
        # [해석] 이름과 직무를 하나의 문장으로 만들어 검색이 잘 되게 합니다.
        chunks.append({
            "type": "header",
            "text": f"[프로필] 이름: {name}, 지원직무: {role}, 지원회사: {company}",
            "metadata": { "source": "resume", "category": "profile" } # [해석] 나중에 출처를 알 수 있게 꼬리표를 답니다.
        })

    # ----------------------------------------------------
    # 3. 학력 (Education)
    # ----------------------------------------------------
    educations = parsed_data.get("education", [])
    for edu in educations: # [문법] 학력이 여러 개(학사, 석사 등)일 수 있으므로 반복문을 돌립니다.
        school = edu.get("school_name", "")
        major = edu.get("major", "")
        period = edu.get("period", "")
        gpa = edu.get("gpa", "")
        status = edu.get("status", "")
        
        # [해석] 흩어진 정보를 하나의 읽기 좋은 문장으로 합칩니다.
        text = f"[학력] {school} {major} ({status})"
        if period: text += f" - {period}"
        if gpa: text += f", 학점: {gpa}"
        
        chunks.append({
            "type": "education",
            "text": text,
            "metadata": { "source": "resume", "category": "education", "school": school }
        })

    # ----------------------------------------------------
    # 4. 대외활동 (Activities)
    # ----------------------------------------------------
    activities = parsed_data.get("activities", [])
    for act in activities:
        org = act.get("organization", "")
        role = act.get("role", "")
        period = act.get("period", "")
        desc = act.get("description", "")
        
        text = f"[대외활동] 기관: {org}, 역할: {role}"
        if period: text += f" ({period})"
        if desc: text += f"\n설명: {desc}"
        
        chunks.append({
            "type": "experience",
            "text": text,
            "metadata": { "source": "resume", "category": "experience", "org": org }
        })

    # ----------------------------------------------------
    # 5. 수상 (Awards)
    # ----------------------------------------------------
    awards = parsed_data.get("awards", [])
    for award in awards:
        title = award.get("title", "")
        org = award.get("organization", "")
        date = award.get("date", "")
        
        text = f"[수상] 상훈: {title}, 기관: {org}"
        if date: text += f" ({date})"
        
        chunks.append({
            "type": "awards",
            "text": text,
            "metadata": { "source": "resume", "category": "awards" }
        })

    # ----------------------------------------------------
    # 6. 자격증 (Certifications) - 🔥 핵심 수정 지점 🔥
    # ----------------------------------------------------
    certifications = parsed_data.get("certifications", [])
    for cert in certifications:
        title = cert.get("title", "")
        org = cert.get("organization", "")
        date = cert.get("date", "")
        
        # [해석] AI가 "자격증을 보유하고 있다"는 것을 확실히 인식하도록 포맷팅합니다.
        text = f"[자격증] 자격명: {title}, 발행기관: {org}"
        if date: text += f" (취득일: {date})"
        
        chunks.append({
            "type": "certifications", 
            "text": text,
            "metadata": { "source": "resume", "category": "certification" }
        })

    # ----------------------------------------------------
    # 7. 프로젝트 (Projects)
    # ----------------------------------------------------
    projects = parsed_data.get("projects", [])
    for proj in projects:
        title = proj.get("title", "")
        period = proj.get("period", "")
        desc = proj.get("description", "")
        
        text = f"[프로젝트] 명칭: {title}"
        if period: text += f" ({period})"
        if desc: text += f"\n상세: {desc}"
        
        # 프로젝트 설명이 길면 텍스트 분할기로 쪼갭니다.
        if len(text) > 400:
            split_texts = text_splitter.split_text(text)
            for i, st in enumerate(split_texts):
                chunks.append({
                    "type": "projects",
                    "text": f"(부분 {i+1}) {st}",
                    "metadata": { "source": "resume", "category": "project", "title": title }
                })
        else:
            chunks.append({
                "type": "projects",
                "text": text,
                "metadata": { "source": "resume", "category": "project" }
            })

    # ----------------------------------------------------
    # 8. 자기소개서 (Self Intro)
    # ----------------------------------------------------
    self_intros = parsed_data.get("self_intro", [])
    for idx, intro in enumerate(self_intros):
        question = intro.get("question", "")
        answer = intro.get("answer", "")
        
        # [해석] 질문은 그 자체로 중요하므로 하나의 조각으로 따로 저장합니다.
        chunks.append({
            "type": "narrative_q",
            "text": f"[자소서 질문{idx+1}] {question}",
            "metadata": { "source": "resume", "category": "narrative", "subtype": "question" }
        })

        # [해석] 답변은 매우 길 수 있습니다! 그래서 위에서 설정한 text_splitter로 쪼갭니다.
        if answer:
            # [문법] split_text(): 긴 답변을 600자 내외의 조각 리스트로 만들어줍니다.
            split_texts = text_splitter.split_text(answer)
            for i, split_text in enumerate(split_texts):
                chunks.append({
                    "type": "narrative_a",
                    "text": f"[자소서 답변{idx+1}-{i+1}] {split_text}",
                    "metadata": {
                        "source": "resume",
                        "category": "narrative",
                        "subtype": "answer",
                        "question_ref": question[:20] + "..." # 어떤 질문에 대한 답인지 맥락 정보를 남김
                    }
                })

    print(f"\n✅ 총 {len(chunks)}개의 청크(Chunk) 생성 완료")
    return chunks

# -----------------------------------------------------------
# 테스트 실행 코드
# -----------------------------------------------------------
if __name__ == "__main__":
    # [해석] 실제 실행하면 파싱 결과를 'chunked_result.json'이라는 파일로 저장해줍니다.
    # 그래야 개발자가 눈으로 조각이 잘 났는지 확인할 수 있으니까요.
    pass
