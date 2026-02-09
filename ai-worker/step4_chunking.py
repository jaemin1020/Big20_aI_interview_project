import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_resume(parsed_data):
    chunks = []
    print("\n[STEP4] 데이터 청킹(Chunking) 시작...")

    # ====================================================
    # ✂️ 텍스트 분할기 설정
    # chunk_size=500: 자소서 등 긴 글을 자를 때 사용
    # chunk_overlap=50: 문맥 유지
    # ====================================================
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=70,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    # ----------------------------------------------------
    # 1. 헤더 (Header)
    # ----------------------------------------------------
    header = parsed_data.get("header", {})
    if header:
        name = header.get("name", "")
        role = header.get("target_role", "")
        company = header.get("target_company", "")
        chunks.append({
            "type": "header",
            "text": f"[프로필] 이름: {name}, 지원직무: {role}, 지원회사: {company}",
            "metadata": { "source": "resume", "category": "profile" }
        })

    # ----------------------------------------------------
    # 2. 학력 (Education)
    # ----------------------------------------------------
    educations = parsed_data.get("education", [])
    for edu in educations:
        school = edu.get("school_name", "")
        major = edu.get("major", "")
        period = edu.get("period", "")
        gpa = edu.get("gpa", "")
        status = edu.get("status", "")
        
        text = f"[학력] {school} {major} ({status})"
        if period: text += f" - {period}"
        if gpa: text += f", 학점: {gpa}"
        
        chunks.append({
            "type": "education",
            "text": text,
            "metadata": { "source": "resume", "category": "education", "school": school }
        })

    # ----------------------------------------------------
    # 3. 활동 및 경력 (Activities)
    # ----------------------------------------------------
    activities = parsed_data.get("activities", [])
    for act in activities:
        org = act.get("organization", "")
        role = act.get("role", "")
        content = act.get("content", "")
        period = act.get("period", "")
        
        text = f"[활동] {content}"
        if org: text += f" ({org})"
        if role: text += f" - {role}"
        if period: text += f" [{period}]"

        chunks.append({
            "type": "activity",
            "text": text,
            "metadata": { "source": "resume", "category": "activity", "org": org }
        })

    # ----------------------------------------------------
    # 4. 수상 (Awards)
    # ----------------------------------------------------
    awards = parsed_data.get("awards", [])
    for awd in awards:
        title = awd.get("title", "")
        grade = awd.get("grade", "")
        org = awd.get("organization", "")
        date = awd.get("date", "")
        
        text = f"[수상] {title}"
        if grade: text += f" ({grade})"
        if org: text += f" - {org}"
        if date: text += f" [{date}]"

        chunks.append({
            "type": "award",
            "text": text,
            "metadata": { "source": "resume", "category": "award" }
        })

    # ----------------------------------------------------
    # 5. 프로젝트 (Projects)
    # ----------------------------------------------------
    projects = parsed_data.get("projects", [])
    for proj in projects:
        title = proj.get("title", "")
        period = proj.get("period", "")
        desc = proj.get("description", "") # 기관 정보 등이 들어있음
        
        text = f"[프로젝트] {title}"
        if period: text += f" ({period})"
        if desc: text += f" - {desc}"

        chunks.append({
            "type": "project",
            "text": text,
            "metadata": { "source": "resume", "category": "project" }
        })

    # ----------------------------------------------------
    # 6. 자격증 (Certifications)
    # ----------------------------------------------------
    certs = parsed_data.get("certifications", [])
    for cert in certs:
        title = cert.get("title", "")
        date = cert.get("date", "")
        org = cert.get("organization", "")

        text = f"[자격증] {title}"
        if date: text += f" ({date})"
        if org: text += f" - {org}"
        
        chunks.append({
            "type": "certification",
            "text": text,
            "metadata": { "source": "resume", "category": "certification" }
        })

    # ----------------------------------------------------
    # 7. 자기소개서 (Self Intro) - 🔥 의미 단위 분할 🔥
    # ----------------------------------------------------
    self_intros = parsed_data.get("self_intro", [])
    for idx, intro in enumerate(self_intros):
        question = intro.get("question", "")
        answer = intro.get("answer", "")
        
        # 질문(Question) 자체도 하나의 청크로 저장 (검색 용이성)
        chunks.append({
            "type": "narrative_q",
            "text": f"[자소서 질문{idx+1}] {question}",
            "metadata": { "source": "resume", "category": "narrative", "subtype": "question" }
        })

        # 답변(Answer)이 길면 쪼개서 저장
        if answer:
            split_texts = text_splitter.split_text(answer)
            for i, split_text in enumerate(split_texts):
                chunks.append({
                    "type": "narrative_a",
                    "text": f"[자소서 답변{idx+1}-{i+1}] {split_text}",
                    "metadata": {
                        "source": "resume",
                        "category": "narrative",
                        "subtype": "answer",
                        "question_ref": question[:20] + "..." # 어떤 질문에 대한 답인지 살짝 표시
                    }
                })

    # 결과 요약 출력
    print(f"\n✅ 총 {len(chunks)}개의 청크(Chunk) 생성 완료")
    return chunks

# -----------------------------------------------------------
# 테스트 실행 코드 (파일로 저장 기능 추가됨)
# -----------------------------------------------------------
if __name__ == "__main__":
    import os
    from step2_parse_resume import parse_resume_final
    
    # 테스트할 파일 경로 확인
    target_pdf = "resume.pdf"
    if not os.path.exists(target_pdf):
        target_pdf = "/app/resume.pdf"
    
    if os.path.exists(target_pdf):
        print(f"📂 파일 로드: {target_pdf}")
        
        # 1. 파싱 (Step 2)
        parsed_data = parse_resume_final(target_pdf)
        
        if parsed_data:
            # 2. 청킹 (Step 4)
            chunks = chunk_resume(parsed_data)
            
            # ----------------------------------------------------
            # [추가됨] 결과를 눈으로 확인하기 위해 파일로 저장
            # ----------------------------------------------------
            output_file = "chunked_result.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ 저장 완료! '{output_file}' 파일을 열어서 전체 내용을 확인해보세요.")
            
            # (선택) 화면에는 3개만 맛보기로 출력
            print("\n--- [청크 예시 (상위 3개)] ---")
            for c in chunks[:3]:
                print(json.dumps(c, indent=2, ensure_ascii=False))
        else:
            print("❌ 파싱 데이터 없음")
    else:
        print("❌ 테스트할 PDF 파일이 없습니다.")