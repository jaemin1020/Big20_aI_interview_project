import logging
import time
import re
import json
import sys
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any
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
    Question,
    update_transcript_sentiment,
    update_transcript_scores,
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

# backend-core 및 하위 utils 경로 추가 (패키지 충돌 방지)
backend_core_path = os.path.abspath(os.path.join(ai_worker_root, "..", "backend-core"))
backend_core_utils = os.path.join(backend_core_path, "utils")
for p in [backend_core_path, backend_core_utils]:
    if p not in sys.path:
        sys.path.insert(0, p)

logger = logging.getLogger("AI-Worker-Evaluator")

# utils.exaone_llm은 실제 사용 시점에 임포트 (워커 시작 시 크래시 방지)
try:
    from utils.exaone_llm import get_exaone_llm
    # rubric_generator는 backend-core/utils에 있음. 
    # ai-worker/utils와 패키지명(utils)이 중복되므로 직접 모듈 임포트 시도
    import rubric_generator
    create_evaluation_rubric = rubric_generator.create_evaluation_rubric
    logger.info("✅ Successfully linked rubric_generator from backend-core")
except ImportError as e:
    logger.warning(f"Could not import from backend-core utils: {e}. Falling back to basics.")

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
    total_score: int = Field(description="루브릭 세부 항목 점수들의 합계 (0-100)")
    rubric_scores: Dict[str, int] = Field(description="루브릭 세부 항목별 점수 (예: {'논리적 구조': 35, '핵심 전달력': 30, ...})")
    feedback: str = Field(description="답변에 대한 구체적이고 건설적인 피드백 (마크다운 없이 평문으로 작성)")

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
        
        # question_type이 직접 넘어온 경우 우선 순위 부여
        if question_type and question_type != "unknown":
            stage_name = question_type

        logger.info(f"🔍 Analyzing Answer: Stage={stage_name}, QuestionID={question_id}")

        # [핵심] 100점 만점 상세 루브릭 우선 적용
        # 기존 (0-5) 척도 루브릭이 넘어오더라도, rubric_generator의 상세 항목이 있다면 그것을 사용합니다.
        real_rubric = get_rubric_for_stage(stage_name)
        if real_rubric:
            rubric = real_rubric
            logger.info(f"📊 Using REAL Detailed Rubric for {stage_name}")
        elif not rubric or "guide" in rubric:
            logger.warning(f"⚠️ No matching detailed rubric found for stage: {stage_name}. Using fallback.")
            if not rubric:
                rubric = {
                    "name": "일반 평가",
                    "detailed_scoring": {"전반적 답변 품질": 100},
                    "scoring_guide": {"excellent": {"range": [85, 100]}}
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

        # 프롬프트 구성 (EXAONE 3.5 최적화)
        system_msg = """[|system|]귀하는 기술력, 소통 능력, 조직 적합성을 정밀 검증하는 'AI 채용 평가 위원회'의 전문 심사관입니다.
LG AI Research가 개발한 EXAONE으로서, 제공된 루브릭을 절대적 기준으로 삼아 지원자의 답변을 냉철하게 분석하고 수치화된 점수와 건설적인 피드백을 산출하십시오.

[평가 가이드라인]
1. **기술적 엄밀성**: 답변에 포함된 기술 개념의 정확성과 선택 근거의 타당성을 최우선으로 검토하십시오.
2. **증거 중심 피드백**: 단순히 느낌을 서술하지 말고, 지원자의 답변 중 어떤 표현이나 사례가 루브릭 지표에 부합했는지 구체적으로 인용하십시오.
3. **수치화**: 루브릭의 점수 배점을 엄격히 준수하여 점수를 산출하되, 논리가 부족하거나 답변이 모호한 경우 보수적으로 평가하십시오.
4. **인재상 반영**: 인재상 정보가 제공된 경우, 지원자의 태도나 가치관이 기업의 지향점과 얼마나 일치하는지 분석 결과에 반드시 포함하십시오.
5. **텍스트 정제 (No Markdown)**: 피드백 작성 시 볼트(**), 이탤릭(*) 등의 마크다운 문법을 절대 사용하지 마십시오. 오직 순수한 평문(Plain Text)으로만 작성하십시오.
6. **중복 표현 및 말더듬 방지**: 문장 끝에서 유사한 어미를 반복하거나, 동일한 단어를 나열하는 등의 환각/말더듬 현상을 철저히 배제하십시오.[|endofturn|]"""

        user_msg = f"""[|user|]다음 질문에 대한 지원자의 답변을 루브릭 기준에 맞춰 정밀 평가하십시오.
        
[질문]
{question_text}

[답변]
{answer_text}

[평가 루브릭]
{json.dumps(rubric, ensure_ascii=False) if rubric else "표준 면접 평가 기준"}{company_ideal_section}

{parser.get_format_instructions()}[|endofturn|]"""
        
        # 생성 및 파싱 (EXAONE 전용 포맷 사용)
        prompt = f"{system_msg}\n{user_msg}\n[|assistant|]"
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

        tech_score = safe_int(result.get("total_score"), 70)
        rubric_scores = result.get("rubric_scores", {})
        
        # 1. 감성 점수 업데이트 (기존 로직 유지용)
        sentiment = (tech_score / 100.0) - 0.5 
        update_transcript_sentiment(
            transcript_id,
            sentiment_score=sentiment,
            emotion="neutral",
            total_score=float(tech_score),
            rubric_score=db_rubric_data
        )
        
        # 2. [핵심] 상세 루브릭 점수 및 총점 칼럼 업데이트 (한글)
        db_rubric_data = {
            "평가영역": rubric.get("name", "일반 평가") if rubric else "일반 평가",
            "세부항목점수": rubric_scores,
            "항목별배점": rubric.get("detailed_scoring", {}) if rubric else {}
        }
        update_transcript_scores(
            transcript_id,
            total_score=float(tech_score),
            rubric_score=db_rubric_data
        )
        
        # 3. 질문 평균 점수 업데이트
        if question_id:
            update_question_avg_score(question_id, tech_score)

        duration = time.time() - start_ts
        logger.info(f"답변 상세 평가 완료 ({duration:.2f}초, 점수: {tech_score})")
        return result

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
            system_msg = f"""[|system|]당신은 대한민국 최고의 기술 기업에서 수만 명의 인재를 발굴해온 '{position}' 분야 전문 채용 위원장입니다.
LG AI Research의 EXAONE으로서, 면접 전체 발화 로그와 [표준 평가 루브릭]을 종합 분석하여 지원자의 최종 합격 여부를 판단할 수 있는 심층 기술 리포트를 작성하십시오.

[핵심 평가 프로토콜]
1. **역량별 매칭 분석**: 루브릭의 평가 지표와 지원자의 답변을 대조하여, 단순히 잘했다는 표현이 아닌 '근거 중심'의 성적표를 작성하십시오.
2. **논리적 일관성 검증**: 인터뷰 전반에 걸쳐 지원자의 답변이 일관된 실무 철학과 기술적 원칙을 유지하고 있는지 체크하십시오.
3. **STAR 기법 기반 검증**: 지원자가 성과를 설명할 때 상황(S)-과업(T)-행동(A)-결과(R) 구조를 갖추어 실질적인 기여도를 증명했는지 평가하십시오.
4. **시니어의 제언**: 강점은 극대화하고 약점은 실천 가능한 성장의 기회로 전환할 수 있도록 시니어 전문가의 깊이 있는 조언(Summary)을 제공하십시오.
5. **텍스트 정제 (No Markdown)**: 전 영역 피드백 및 강점/보완점 작성 시 볼트(**), 이탤릭(*), 리스트(-) 등의 마크다운 문법을 일절 사용하지 마십시오. 오직 순수한 평문(Plain Text)으로만 서술하십시오.
6. **언어 일관성 및 중복 방지**: 전문적이고 정제된 어조를 유지하되, 동일한 문구나 수식어가 반복되어 가독성을 해치는 현상을 방지하십시오.[|endofturn|]"""

            user_msg = f"""[|user|]다음 면접 대화 전문을 바탕으로 루브릭 기준에 따라 최종 기술 역량 평가 리포트를 생성하십시오.
            
[면접 대화 전문]
{conversation}

[표준 평가 루브릭]
{json.dumps(full_rubric, ensure_ascii=False, indent=2)}

[출력 제약 사항]
- 모든 분석은 반드시 루브릭의 세부 목표와 연동되어야 합니다.
- strengths와 improvements 항목은 면접 중 특정 발화를 근거로 인용하여 2문장 이상의 서술형으로 작성하십시오.
- 결과물은 반드시 지정된 JSON 포맷만 출력하며, 사족을 붙이지 마십시오.

{parser.get_format_instructions()}[|endofturn|]"""
            
            # 생성 및 파싱 (EXAONE 전용 포맷 사용)
            prompt = f"{system_msg}\n{user_msg}\n[|assistant|]"
            # 리포트는 내용이 길므로 max_tokens를 넉넉하게 설정
            raw_output = exaone.invoke(prompt, temperature=0.3, max_tokens=3000)
            
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
