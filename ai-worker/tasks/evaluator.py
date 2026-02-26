import logging
import time
import re
import json
import sys
import os
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import JsonOutputParser
from celery import shared_task

# DB Helper Functions
from db import (
    engine,
    Session,
    Transcript,
    Interview,
    Company,
    Resume,
    update_transcript_sentiment,
    update_question_avg_score,
    get_interview_transcripts,
    get_user_answers
)
from sqlmodel import select

# 9~14번 스테이지: 인재상(ideal) 참고가 필요한 stage 목록
# interview_scenario_transition.py의 order 9~14에 해당
COMPANY_IDEAL_STAGES = {
    "communication",          # 9. 협업/소통 질문
    "communication_followup", # 10. 협업 심층
    "responsibility",         # 11. 가치관/책임감 질문
    "responsibility_followup",# 12. 가치관 심층
    "growth",                 # 13. 성장가능성 질문
    "growth_followup",        # 14. 성장가능성 심층
}

# AI-Worker 루트 디렉토리를 찾아 sys.path에 추가
current_file_path = os.path.abspath(__file__) # tasks/evaluator.py
tasks_dir = os.path.dirname(current_file_path) # tasks/
ai_worker_root = os.path.dirname(tasks_dir)    # ai-worker/

# backend-core 경로 추가 (rubric_generator 임포트를 위함)
backend_core_path = os.path.abspath(os.path.join(ai_worker_root, "..", "backend-core"))
if backend_core_path not in sys.path:
    sys.path.insert(0, backend_core_path)

logger = logging.getLogger("AI-Worker-Evaluator")

# utils.exaone_llm은 실제 사용 시점에 임포트 (워커 시작 시 크래시 방지)
try:
    from utils.exaone_llm import get_exaone_llm
    from utils.rubric_generator import create_evaluation_rubric
except ImportError:
    logger.warning("Could not import from backend-core utils. Falling back to basics.")

def get_rubric_for_stage(stage_name: str) -> dict:
    """스테이지 이름에 맞는 루브릭 영역 반환"""
    try:
        full_rubric = create_evaluation_rubric()
        for area in full_rubric["evaluation_areas"]:
            if stage_name in area["target_stages"]:
                logger.info(f"✅ Found matching Rubric Area: {area['name']} for stage: {stage_name}")
                return area
    except Exception as e:
        logger.error(f"Error mapping rubric for stage {stage_name}: {e}")
    return None

# -----------------------------------------------------------
# [Schema] 평가 데이터 구조 정의 (Pydantic)
# -----------------------------------------------------------
class AnswerEvalSchema(BaseModel):
    technical_score: int = Field(description="기술적 지식 및 숙련도 점수 (0-5)")
    communication_score: int = Field(description="의사소통 및 전달 능력 점수 (0-5)")
    feedback: str = Field(description="답변에 대한 구체적이고 건설적인 피드백")

class FinalReportSchema(BaseModel):
    overall_score: int = Field(description="전체 평균 점수 (0-100)")
    technical_score: int = Field(description="기술 이해도 (0-100)")
    experience_score: int = Field(description="직무 경험 (0-100)")
    problem_solving_score: int = Field(description="문제 해결 (0-100)")
    communication_score: int = Field(description="의사소통 (0-100)")
    responsibility_score: int = Field(description="책임감 (0-100)")
    growth_score: int = Field(description="성장 의지 (0-100)")
    
    technical_feedback: str = Field(description="기술 원리 및 선택 근거에 대한 분석")
    experience_feedback: str = Field(description="직무 경험의 구체성과 실무 연계성에 대한 평가")
    problem_solving_feedback: str = Field(description="STAR 기법에 기반한 논리적 전개 능력 분석")
    communication_feedback: str = Field(description="전문어 사용의 적절성 및 메시지 전달력 평가")
    responsibility_feedback: str = Field(description="답변의 일관성 및 업무에 임하는 책임감 분석")
    growth_feedback: str = Field(description="자기계발 의지 및 향후 발전 가능성에 대한 제언")

    strengths: List[str] = Field(
        description="지원자의 주요 강점 2-3가지. 각 항목은 면접 답변에서 구체적인 근거를 인용하여 2문장 이상의 완결된 서술형 문장으로 작성하십시오. 예: '프로젝트에서 RAG 도입의 타당성을 실험 데이터로 직접 검증한 점은 기술력과 분석 능력을 동시에 보여줍니다. 특히 키워드 검색 대비 벡터 검색의 hit rate를 수치로 비교한 접근 방식은 실무 역량을 증명합니다.'"
    )
    improvements: List[str] = Field(
        description="보완이 필요한 약점 및 개선점 2-3가지. 각 항목은 면접 중 드러난 구체적인 사례를 인용하여 2문장 이상의 완결된 서술형 문장으로 작성하십시오. 단순 키워드나 나열식 표현은 금지합니다."
    )
    summary_text: str = Field(description="성장을 위한 시니어 위원장의 최종 한마디 (3문장 내외)")

@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question_text: str, answer_text: str, rubric: dict = None, question_id: int = None, question_type: str = None):
    """개별 답변 평가 및 실시간 다음 질문 생성 트리거"""
    
    start_ts = time.time()
    
    try:
        # 질문 정보 조회 (Stage 확인용)
        stage_name = "unknown"
        if question_id:
            with Session(engine) as session:
                question = session.get(Question, question_id)
                if question:
                    stage_name = question.question_type or "unknown"

        # [핵심] 기존의 잘못된 'guide' 루브릭 대신, rubric_generator의 진짜 루브릭 사용
        if not rubric or "guide" in rubric:
            real_rubric = get_rubric_for_stage(stage_name)
            if real_rubric:
                rubric = real_rubric
                logger.info(f"📊 Using REAL Rubric for {stage_name}")

        if not answer_text or not answer_text.strip():
            logger.warning(f"대화 내역 {transcript_id}의 답변이 비어 있습니다. LLM 평가를 건너뜁니다.")
            return {
                "technical_score": 0,
                "communication_score": 0,
                "feedback": "답변이 제공되지 않았습니다."
            }
        
        # LangChain Parser 설정
        parser = JsonOutputParser(pydantic_object=AnswerEvalSchema)
        
        # 엔진 가져오기
        llm_engine = get_exaone_llm()
        
        # ── 인재상(ideal) 조회 (9~14번 스테이지만) ────────────────────────
        company_ideal_section = ""
        if question_type in COMPANY_IDEAL_STAGES:
            try:
                with Session(engine) as session:
                    transcript_obj = session.get(Transcript, transcript_id)
                    if transcript_obj:
                        interview_obj = session.get(Interview, transcript_obj.interview_id)
                        if interview_obj:
                            company_obj = None

                            # ① company_id가 있으면 직접 조회
                            if interview_obj.company_id:
                                company_obj = session.get(Company, interview_obj.company_id)

                            # ② company_id 없으면 이력서의 target_company 이름으로 검색 (fallback)
                            if not company_obj and interview_obj.resume_id:
                                resume_obj = session.get(Resume, interview_obj.resume_id)
                                if resume_obj and resume_obj.structured_data:
                                    target_company = resume_obj.structured_data.get("header", {}).get("target_company", "")
                                    if target_company:
                                        # 공백 제거 후 완전 일치 매칭
                                        # 예) "삼성전자 DS부문" == "삼성전자DS부문" (공백만 무시, 글자는 정확히 일치)
                                        from sqlmodel import select as sql_select
                                        normalized_target = target_company.replace(" ", "").lower()
                                        all_companies = session.exec(sql_select(Company)).all()
                                        company_obj = next(
                                            (c for c in all_companies
                                             if c.company_name and
                                             c.company_name.replace(" ", "").lower() == normalized_target),
                                            None
                                        )
                                        if company_obj:
                                            logger.info(f"📄 '{target_company}' → '{company_obj.company_name}' 매칭 성공")

                            if company_obj and company_obj.ideal:
                                company_ideal_section = f"""

[회사 인재상 참고]
지원 회사: {company_obj.company_name}
인재상: {company_obj.ideal}
※ 위 인재상과의 부합 여부를 평가 시 반드시 반영하십시오."""
                                logger.info(f"✅ [{question_type}] 인재상 로드 - {company_obj.company_name}")
            except Exception as ideal_err:
                logger.warning(f"⚠️ 인재상 조회 실패 (평가는 계속 진행): {ideal_err}")

        # 프롬프트 구성
        system_msg = "귀하는 전문 면접관이며, 지원자의 답변을 기술력과 의사소통 관점에서 평가합니다."
        user_msg = f"""다음 질문에 대한 지원자의 답변을 루브릭 기준에 맞춰 평가하십시오.
        
[질문]
{question_text}

[답변]
{answer_text}

[평가 루브릭]
{json.dumps(rubric, ensure_ascii=False) if rubric else "표준 면접 평가 기준"}{company_ideal_section}

{parser.get_format_instructions()}"""
        
        # 생성 및 파싱
        prompt = llm_engine._create_prompt(system_msg, user_msg)
        raw_output = llm_engine.invoke(prompt, temperature=0.2)
        
        try:
            result = parser.parse(raw_output)
        except Exception as parse_err:
            logger.error(f"Failed to parse LLM output: {parse_err}")
            # 폴백: 정규표현식 시도 또는 기본값
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"technical_score": 3, "communication_score": 3, "feedback": "평가 데이터를 파싱할 수 없습니다."}
        
        def safe_int(v, default=3):
            try:
                if v is None: return default
                return int(float(v))
            except (ValueError, TypeError):
                return default

        tech_score = safe_int(result.get("technical_score"), 3)
        comm_score = safe_int(result.get("communication_score"), 3)
        sentiment = ((tech_score + comm_score) / 10.0) - 0.5 
        
        update_transcript_sentiment(
            transcript_id, 
            sentiment_score=sentiment, 
            emotion="neutral"
        )
        
        answer_quality = (tech_score + comm_score) * 10 
        
        if question_id:
            update_question_avg_score(question_id, answer_quality)

        duration = time.time() - start_ts
        logger.info(f"답변 평가 완료 ({duration:.2f}초, Stage: {stage_name})")
        return result

    except Exception as e:
        logger.error(f"Evaluation Failed: {e}")
        return {"error": str(e)}

    except Exception as e:
        logger.error(f"Evaluation Failed: {e}")
        return {"error": str(e)}

@shared_task(name="tasks.evaluator.generate_final_report")
def generate_final_report(interview_id: int):
    """
    최종 평가 보고서 생성 (시니어 면접관 페르소나 적용)
    """
    logger.info(f"Generating Final Report for Interview {interview_id}")
    from db import (
        Interview, 
        create_or_update_evaluation_report, 
        update_interview_overall_score, 
        get_interview_transcripts
    )
    
    try:
        transcripts = get_interview_transcripts(interview_id)
        logger.info(f"📊 Found {len(transcripts)} transcripts for Interview {interview_id}")
        
        # 🧹 메모리 청소 (리포트 분석 전 공간 확보)
        import gc
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        # 인터뷰 포지션 정보 가져오기
        with Session(engine) as session:
            interview = session.get(Interview, interview_id)
            position = interview.position if interview else "지원 직무"

        if not transcripts:
            logger.warning("이 인터뷰에 대한 대화 내역을 찾을 수 없습니다.")
            create_or_update_evaluation_report(
                interview_id,
                technical_score=0, communication_score=0, cultural_fit_score=0,
                summary_text="기록된 대화가 없어 리포트를 생성할 수 없습니다.",
                details_json={"error": "no_data"}
            )
            return

        conversation = "\n".join([f"{t.speaker}: {t.text}" for t in transcripts])
        if len(conversation) > 12000: # 대략 8000 토큰 내외로 자름 (안전 계수)
            logger.info(f"⚠️ Conversation too long ({len(conversation)} chars). Truncating: front 3000 + tail 8000.")
            # 중후반부(경험/문제해결/협업/가치관/성장 Q&A)를 최대한 보존하기 위해
            # 앞 3000자(소개/도입)보다 마지막 8000자(핵심 역량) 위주로 유지
            conversation = conversation[:3000] + "\n... (중략 - 도입부 생략) ...\n" + conversation[-8000:]

        try:
            # LangChain Parser 설정
            parser = JsonOutputParser(pydantic_object=FinalReportSchema)
            
            # [핵심] 전체 평가 루브릭 가져오기
            full_rubric = {}
            try:
                full_rubric = create_evaluation_rubric()
                logger.info("📋 Full Rubric loaded for Final Report")
            except Exception as re_err:
                logger.error(f"Failed to load full rubric: {re_err}")

            logger.info(f"🤖 Starting [FINAL REPORT] LLM analysis for Interview {interview_id}...")
            exaone = get_exaone_llm()
            system_msg = f"""당신은 대한민국 최고의 기술 기업에서 수천 명의 지원자를 검증해온 '{position}' 분야 시니어 면접관 위원회의 위원장입니다. 
당신의 임무는 제공된 면접 로그와 [표준 평가 루브릭]을 바탕으로 지원자의 역량을 6개 핵심 지표로 정밀 평가하는 것입니다.

[표준 평가 루브릭]
{json.dumps(full_rubric, ensure_ascii=False, indent=2)}

[평가 지침]
1. 위 루브릭의 '평가 기준(Criteria)'과 '등급별 지표(Indicators)'를 엄격히 준수하여 점수를 산출하십시오.
2. STAR 분석: 지원자가 답변에서 구체적인 상황(S), 과업(T), 행동(A), 결과(R)를 논리적으로 설명했는지 분석하십시오.
3. 기술적 정합성: {position} 직무에 필요한 핵심 기술 원리와 선택 근거를 명확히 알고 있는지 체크하십시오.
4. 피드백 전문성: 단순 칭찬보다는 루브릭의 지표를 근거로 보완할 점을 구체적으로 제시하여 지원자의 성장을 돕는 '시니어의 조언' 톤을 유지하십시오."""

            user_msg = f"""다음 면접 대화 내용을 기반으로 루브릭 기준에 따라 최종 평가를 내리십시오.
            
[면접 대화]
{conversation}

[제약 사항]
- 결과는 반드시 시스템 연동을 위해 지정된 JSON 포맷으로만 출력하십시오.
- 각 점수는 0점에서 100점 사이로 산출하십시오.
- strengths와 improvements는 루브릭의 지표를 참고하여 각각 2-3가지 문자열 배열([])로 작성하십시오.

{parser.get_format_instructions()}"""
            
            # 생성 및 파싱
            prompt = exaone._create_prompt(system_msg, user_msg)
            raw_output = exaone.invoke(prompt, temperature=0.3)
            
            if not raw_output:
                raise ValueError("LLM generated empty output (possibly context limit reached)")

            try:
                result = parser.parse(raw_output)
            except Exception as parse_err:
                logger.error(f"최종 리포트 파싱 실패: {parse_err}")
                json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise parse_err
                
        except Exception as llm_err:
            logger.error(f"LLM Summary failed: {llm_err}")
            # 개별 답변들의 점수가 있다면 그것들의 평균으로 폴백
            try:
                user_transcripts = [t for t in transcripts if t.speaker == 'User']
                valid_scores = []
                for t in user_transcripts:
                    try:
                        s = float(t.sentiment_score) if t.sentiment_score is not None else 0.0
                        valid_scores.append(s + 0.5)
                    except:
                        valid_scores.append(0.5) # 기본 점수
                
                avg_tech = (sum(valid_scores) / len(valid_scores)) * 100 if valid_scores else 70
            except:
                avg_tech = 70
            
            result = {
                "overall_score": int(avg_tech),
                "technical_score": int(avg_tech), 
                "experience_score": int(avg_tech), "problem_solving_score": int(avg_tech),
                "communication_score": int(avg_tech), "responsibility_score": int(avg_tech), "growth_score": int(avg_tech),
                "summary_text": "면접 데이터 분석 중 일시적인 지연이 발생하여 종합 점수 위주로 산출되었습니다. 상세 분석은 답변의 품질을 기반으로 요약되었습니다.",
                "technical_feedback": "기술적 핵심 원리에 대한 이해도가 확인되었습니다.",
                "experience_feedback": "프로젝트 경험의 구체적인 내용이 확인되었습니다.",
                "problem_solving_feedback": "논리적인 문제 해결 과정이 확인되었습니다.",
                "communication_feedback": "전반적인 의사소통 능력이 양호합니다.",
                "responsibility_feedback": "직무에 임하는 태도가 안정적입니다.",
                "growth_feedback": "지속적인 성장 가능성이 엿보입니다.",
                "strengths": ["성실한 답변 참여"], "improvements": ["상세 피드백 기술 지원 필요"]
            }

        try:
            def ensure_int(val, default=0):
                try:
                    if val is None: return default
                    return int(float(str(val)))
                except:
                    return default

            # DB 저장을 위해 점수 추출 (안전한 변환)
            tech = ensure_int(result.get("technical_score"), 0)
            comm = ensure_int(result.get("communication_score"), 0)
            # cultural_fit은 responsibility와 growth의 평균으로 임시 계산 (DB 컬럼 호환성)
            resp = ensure_int(result.get("responsibility_score"), 0)
            grow = ensure_int(result.get("growth_score"), 0)
            cult = int((resp + grow) / 2)
            overall = ensure_int(result.get("overall_score"), int((tech + comm + cult) / 3))

            # 모든 상세 필드를 details_json에 저장 (프론트엔드 연동)
            details = {
                "experience_score": ensure_int(result.get("experience_score"), 0),
                "problem_solving_score": ensure_int(result.get("problem_solving_score"), 0),
                "responsibility_score": resp,
                "growth_score": grow,
                "technical_feedback": result.get("technical_feedback", ""),
                "experience_feedback": result.get("experience_feedback", ""),
                "problem_solving_feedback": result.get("problem_solving_feedback", ""),
                "communication_feedback": result.get("communication_feedback", ""),
                "responsibility_feedback": result.get("responsibility_feedback", ""),
                "growth_feedback": result.get("growth_feedback", ""),
                "strengths": result.get("strengths", []),
                "improvements": result.get("improvements", [])
            }

            create_or_update_evaluation_report(
                interview_id,
                technical_score=tech,
                communication_score=comm,
                cultural_fit_score=cult,
                summary_text=result.get("summary_text", ""),
                details_json=details
            )
            update_interview_overall_score(interview_id, score=overall)
            logger.info(f"✅ 인터뷰 {interview_id}에 대한 최종 리포트 생성 완료")

        except Exception as save_err:
            logger.error(f"Failed to process/save report results: {save_err}")
            raise save_err

    except Exception as e:
        logger.error(f"❌ Error in generate_final_report: {e}")
        create_or_update_evaluation_report(
            interview_id,
            technical_score=0, summary_text="리포트 생성 중 데이터 처리에 오류가 발생했습니다. 잠시 후 명세서를 다시 조회해 주세요."
        )
