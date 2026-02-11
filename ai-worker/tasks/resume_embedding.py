"""
이력서 멀티 섹션 임베딩 생성 Celery Task
기존 청크 기반 임베딩과 병행하여 섹션별 구조화된 임베딩 생성
"""
from celery import shared_task
from sqlmodel import Session
from db import Resume, engine
from utils.resume_embedder import get_resume_embedder
from datetime import datetime
import logging
import json

logger = logging.getLogger("ResumeEmbeddingTask")


@shared_task(bind=True, name="generate_resume_embeddings")
def generate_resume_embeddings_task(self, resume_id: int):
    """
    이력서 멀티 섹션 임베딩 생성 Task
    
    Args:
        resume_id: Resume ID
        
    Returns:
        dict: 임베딩 생성 결과
    
    Raises:
        ValueError: 
        
    생성자: ejm
    생성일자: 2026-02-07
    """
    logger.info(f"[Task {self.request.id}] Resume {resume_id} 멀티 섹션 임베딩 생성 시작")
    
    try:
        # 1. Resume 레코드 조회
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found")
                return {"status": "error", "message": "Resume not found"}
            
            # structured_data가 없으면 에러
            if not resume.structured_data:
                logger.error(f"Resume {resume_id} has no structured_data")
                return {"status": "error", "message": "Resume not parsed yet"}
        
        # 2. 이력서 임베더 가져오기
        embedder = get_resume_embedder()
        
        # 3. structured_data를 기반으로 임베딩 생성
        logger.info(f"[Resume {resume_id}] 멀티 섹션 임베딩 생성 중...")
        
        # structured_data를 resume_data 형식으로 변환
        resume_data = {
            "resume_id": str(resume_id),
            "profile": {
                "target_position": resume.structured_data.get("target_position", ""),
                "target_company": resume.structured_data.get("target_company", ""),
            },
            # structured_data에서 데이터 매핑
            "education": resume.structured_data.get("education", []),
            "experience": resume.structured_data.get("experience", []),
            "projects": resume.structured_data.get("projects", []),
            "skills": resume.structured_data.get("skills", {}),
            "certifications": resume.structured_data.get("certifications", []),
            "cover_letter": resume.structured_data.get("cover_letter", {}),
            "languages": resume.structured_data.get("languages", [])
        }
        
        # extracted_text에서 섹션 정보 추출 (간단한 예시)
        # 실제로는 더 정교한 파싱이 필요할 수 있음
        # if resume.extracted_text:
            # 섹션별로 분리된 데이터가 있다면 활용
            # 여기서는 기본 구조만 생성
            # resume_data["experience"] = []
            # resume_data["projects"] = []
            # resume_data["education"] = []
            # resume_data["self_introduction"] = []
            # resume_data["certifications"] = []
            # resume_data["languages"] = []
            # resume_data["skills"] = {}
        
        # 3.1 임베딩 생성용 데이터 검증
        from utils.validation import ResumeValidator
        data_valid, data_error = ResumeValidator.validate_resume_data_for_embedding(resume_data)
        if not data_valid:
            logger.error(f"[Resume {resume_id}] 임베딩 데이터 검증 실패: {data_error}")
            return {
                "status": "error", 
                "message": f"Embedding data validation failed: {data_error}",
                "resume_id": resume_id
            }
        
        # 임베딩 생성
        embedding_result = embedder.build_resume_embeddings(resume_data)
        
        # 4. ResumeSectionEmbedding 테이블에 저장
        logger.info(f"[Resume {resume_id}] 섹션 임베딩 DB 저장 중...")
        
        from db import ResumeSectionEmbedding, ResumeSectionType
        
        saved_count = 0
        
        try:
            with Session(engine) as session:
                embeddings = embedding_result["embeddings"]
                
                # 프로필
                if "vector" in embeddings.get("profile", {}):
                    section_emb = ResumeSectionEmbedding(
                        resume_id=resume_id,
                        section_type=ResumeSectionType.PROFILE,
                        section_index=0,
                        section_id="profile",
                        content=embeddings["profile"].get("text", ""),
                        embedding=embeddings["profile"]["vector"],
                        section_metadata={"role": embedding_result.get("role", "")}
                    )
                    session.add(section_emb)
                    saved_count += 1
                
                # 경력
                for idx, exp in enumerate(embeddings.get("experience", [])):
                    if "vector" in exp:
                        section_emb = ResumeSectionEmbedding(
                            resume_id=resume_id,
                            section_type=ResumeSectionType.EXPERIENCE,
                            section_index=idx,
                            section_id=exp.get("id", f"exp_{idx}"),
                            content=exp.get("text", ""),
                            embedding=exp["vector"]
                        )
                        session.add(section_emb)
                        saved_count += 1
                
                # 프로젝트
                for idx, proj in enumerate(embeddings.get("projects", [])):
                    if "vector" in proj:
                        section_emb = ResumeSectionEmbedding(
                            resume_id=resume_id,
                            section_type=ResumeSectionType.PROJECT,
                            section_index=idx,
                            section_id=proj.get("id", f"proj_{idx}"),
                            content=proj.get("text", ""),
                            embedding=proj["vector"]
                        )
                        session.add(section_emb)
                        saved_count += 1
                
                # 학력
                for idx, edu in enumerate(embeddings.get("education", [])):
                    if "vector" in edu:
                        section_emb = ResumeSectionEmbedding(
                            resume_id=resume_id,
                            section_type=ResumeSectionType.EDUCATION,
                            section_index=idx,
                            section_id=edu.get("id", f"edu_{idx}"),
                            content=edu.get("text", ""),
                            embedding=edu["vector"]
                        )
                        session.add(section_emb)
                        saved_count += 1
                
                # 자기소개
                for idx, si in enumerate(embeddings.get("self_introduction", [])):
                    if "vector" in si:
                        section_emb = ResumeSectionEmbedding(
                            resume_id=resume_id,
                            section_type=ResumeSectionType.SELF_INTRODUCTION,
                            section_index=idx,
                            section_id=f"si_{idx}",
                            content=si.get("text", ""),
                            embedding=si["vector"],
                            si_type=si.get("type", "기타")
                        )
                        session.add(section_emb)
                        saved_count += 1
                
                # 자격증
                if "vector" in embeddings.get("certifications", {}):
                    section_emb = ResumeSectionEmbedding(
                        resume_id=resume_id,
                        section_type=ResumeSectionType.CERTIFICATION,
                        section_index=0,
                        section_id="certifications",
                        content=embeddings["certifications"].get("text", ""),
                        embedding=embeddings["certifications"]["vector"]
                    )
                    session.add(section_emb)
                    saved_count += 1
                
                # 어학
                if "vector" in embeddings.get("languages", {}):
                    section_emb = ResumeSectionEmbedding(
                        resume_id=resume_id,
                        section_type=ResumeSectionType.LANGUAGE,
                        section_index=0,
                        section_id="languages",
                        content=embeddings["languages"].get("text", ""),
                        embedding=embeddings["languages"]["vector"]
                    )
                    session.add(section_emb)
                    saved_count += 1
                
                # 기술 스택
                if "vector" in embeddings.get("skills", {}):
                    section_emb = ResumeSectionEmbedding(
                        resume_id=resume_id,
                        section_type=ResumeSectionType.SKILL,
                        section_index=0,
                        section_id="skills",
                        content=embeddings["skills"].get("text", ""),
                        embedding=embeddings["skills"]["vector"]
                    )
                    session.add(section_emb)
                    saved_count += 1
                
                # 모든 임베딩 저장 완료 후 커밋
                session.commit()
                logger.info(f"[Resume {resume_id}] {saved_count}개 섹션 임베딩 저장 완료")
        
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 임베딩 저장 실패: {e}", exc_info=True)
            # 세션은 자동으로 롤백됨 (context manager)
            return {
                "status": "error",
                "message": f"Failed to save embeddings: {e}",
                "resume_id": resume_id
            }
        
        # 통계 정보 수집
        stats = {
            "profile": 1 if embedding_result["embeddings"].get("profile", {}).get("vector") else 0,
            "experience": len(embedding_result["embeddings"].get("experience", [])),
            "projects": len(embedding_result["embeddings"].get("projects", [])),
            "education": len(embedding_result["embeddings"].get("education", [])),
            "self_introduction": len(embedding_result["embeddings"].get("self_introduction", [])),
            "certifications": 1 if embedding_result["embeddings"].get("certifications", {}).get("vector") else 0,
            "languages": 1 if embedding_result["embeddings"].get("languages", {}).get("vector") else 0,
            "skills": 1 if embedding_result["embeddings"].get("skills", {}).get("vector") else 0,
        }
        
        total_embeddings = sum(stats.values())
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "total_embeddings": total_embeddings,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"[Resume {resume_id}] 멀티 섹션 임베딩 생성 실패: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@shared_task(name="search_resume_sections")
def search_resume_sections_task(resume_id: int, query: str, top_k: int = 3, section_types: list = None):
    """
    이력서 섹션 검색 Task (DB 벡터 유사도 검색)
    
    Args:
        resume_id: Resume ID
        query: 검색 쿼리
        top_k: 반환할 상위 결과 개수
        section_types: 검색할 섹션 타입 리스트 (None이면 전체 검색)
        
    Returns:
        dict: 검색 결과
    
    Raises:
        ValueError: 검색실패

    생성자: ejm
    생성일자: 2026-02-07
    """
    logger.info(f"Resume {resume_id}에서 '{query}' 검색 시작")
    
    try:
        from db import ResumeSectionEmbedding, ResumeSectionType, engine
        from sqlmodel import select
        from utils.vector_utils import get_embedding_generator
        
        # 1. 쿼리 임베딩 생성
        generator = get_embedding_generator()
        query_vector = generator.encode_query(query)
        
        # 2. DB에서 벡터 유사도 검색
        with Session(engine) as session:
            # Distance(거리) 계산 표현식 (pgvector)
            dist_expr = ResumeSectionEmbedding.embedding.cosine_distance(query_vector)
            
            # 섹션과 거리를 함께 조회
            stmt = select(ResumeSectionEmbedding, dist_expr.label("distance")).where(
                ResumeSectionEmbedding.resume_id == resume_id,
                ResumeSectionEmbedding.embedding.isnot(None)
            )
            
            # 섹션 타입 필터링
            if section_types:
                stmt = stmt.where(ResumeSectionEmbedding.section_type.in_(section_types))
            
            # 거리순 정렬 (유사도 높은 순)
            stmt = stmt.order_by(dist_expr).limit(top_k)
            
            rows = session.exec(stmt).all()
            
            # 결과 포맷팅
            results = []
            for section, distance in rows:
                # 코사인 거리를 유사도로 변환 (1 - distance/2)
                # distance 범위: 0(일치)~2(반대)
                similarity = 1 - (distance / 2)
                
                results.append({
                    "section": section.section_type.value if hasattr(section.section_type, "value") else section.section_type,
                    "section_id": section.section_id,
                    "section_index": section.section_index,
                    "text": section.content,
                    "similarity": float(similarity),
                    "si_type": section.si_type if section.section_type == ResumeSectionType.SELF_INTRODUCTION else None,
                    "section_metadata": section.section_metadata,
                    "created_at": str(section.created_at)
                })
        
        logger.info(f"Resume {resume_id} 검색 완료: {len(results)}개 결과")
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "query": query,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Resume {resume_id} 검색 실패: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# 사용 예시
if __name__ == "__main__":
    # 테스트
    result = generate_resume_embeddings_task(1)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 검색 테스트
    search_result = search_resume_sections_task(1, "프로젝트 경험", top_k=3)
    print(json.dumps(search_result, indent=2, ensure_ascii=False))
