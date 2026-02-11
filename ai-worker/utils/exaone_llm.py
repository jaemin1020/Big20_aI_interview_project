"""
EXAONE-3.5-7.8B-Instruct 통합 LLM 모듈 (GGUF 버전)
질문 생성 및 답변 평가를 하나의 모델로 처리
Llama.cpp 엔진 사용으로 CPU/GPU 효율적 실행
"""
import os
import logging
import json
import re
from typing import Optional, Dict, List
from llama_cpp import Llama

logger = logging.getLogger("EXAONE-LLM")

# 모델 경로 (컨테이너 내부 경로)
MODEL_PATH = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

class ExaoneLLM:
    """
    EXAONE-3.5-7.8B-Instruct (GGUF) 싱글톤 LLM
    
    Attributes:
        llm (Llama): Llama.cpp 모델 인스턴스
        _initialized (bool): 초기화 여부
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        logger.info(f"🚀 Loading EXAONE GGUF Model from: {MODEL_PATH}")
        
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

        # Llama.cpp 모델 로드
        try:
            # 환경변수에서 GPU 레이어 설정 로드 (기본값 -1: 전체 GPU 사용)
            gpu_layers = int(os.getenv("N_GPU_LAYERS", "-1"))
            logger.info(f"⚙️ Configured N_GPU_LAYERS: {gpu_layers}")

            self.llm = Llama(
                model_path=MODEL_PATH,
<<<<<<< HEAD
                n_gpu_layers=-1,      # 가능한 모든 레이어를 GPU로 오프로드
                n_ctx=2048,           # 컨텍스트 윈도우 크기 (메모리 절약)
                n_batch=128,          # 배치 크기 (CPU 반응성 향상)
=======
                n_gpu_layers=gpu_layers,
                n_ctx=4096,           # 컨텍스트 윈도우 크기
                n_batch=512,          # 배치 크기
>>>>>>> Phase_3
                verbose=False          # 로딩 로그 출력
            )
            logger.info(f"✅ EXAONE GGUF Model Initialized (GPU Layers: {gpu_layers})")
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {e}")
            raise e
        
        self._initialized = True
    
    def _create_prompt(self, system_msg: str, user_msg: str) -> str:
        """EXAONE 3.5 프롬프트 포맷 적용"""
        return f"[|system|]{system_msg}[|endofturn|]\n[|user|]{user_msg}[|endofturn|]\n[|assistant|]"

    def generate_questions(
        self,
        target_role: str,
        context: str = "",
        examples: List[str] = None,
        count: int = 1
    ) -> List[str]:
        """면접 질문 생성
        
        Args:
            target_role (str): 직무 포지션
            context (str, optional): 추가 컨텍스트. Defaults to "".
            examples (List[str], optional): 예시 질문. Defaults to None.
            count (int, optional): 생성할 질문 수. Defaults to 1.
            
        Returns:
            List[str]: 생성된 질문 리스트
        
        생성자: ejm
        생성일자: 2026-02-04
        """
        # Few-shot 예시
        if examples:
            few_shot = "\n".join([f"- {q}" for q in examples[:3]])
        else:
            few_shot = "- React의 Virtual DOM이 무엇인지 설명해주세요.\n- HTTP와 HTTPS의 차이점은 무엇인가요?\n- 본인이 경험한 가장 큰 기술적 문제는 무엇이었나요?"
        
        context_str = f"\n\n추가 컨텍스트:\n{context}" if context else ""
        
        system_msg = "당신은 지원자의 이력서를 꼼꼼히 읽고 날카로운 질문을 던지는 면접관입니다. 일반적인 질문은 배제하고, 반드시 이력서에 기재된 구체적인 사실(프로젝트, 경력, 학력 등)을 근거로 질문하세요."
        user_msg = f"""[지원 직무]: {target_role}
[지원자 이력서 내용]: 
{context_str}

위 지원자의 이력서 내용을 바탕으로 맞춤형 면접 질문 {count}개를 생성하세요.

[필수 요구사항]
1. **이력서에 없는 내용은 묻지 마세요.** (예: 하지도 않은 클라우드 경험을 묻는 등)
2. 반드시 **"이력서에 ~라고 기재하셨는데", "~ 프로젝트에서 ~를 하셨다고 했는데"**와 같이 이력서 내용을 직접 언급하며 질문을 시작하세요.
3. 지원자의 **실제 기술 스택과 활동**에 집중해서 질문하세요.
4. 질문은 한 줄에 하나씩, 총 {count}개를 작성하세요.
5. 질문 이외의 사족은 생략하세요.

질문 리스트:"""

        prompt = self._create_prompt(system_msg, user_msg)
        
        try:
            output = self.llm(
                prompt,
<<<<<<< HEAD
                max_tokens=300,
                stop=["[|endofturn|]", "[|user|]", "생성된 질문:"],
=======
                max_tokens=1024,
                stop=["[|endofturn|]", "[|user|]"],
>>>>>>> Phase_3
                temperature=0.7,
                top_p=0.9,
                echo=False
            )
            
            response_text = output['choices'][0]['text'].strip()
            
            # 후처리 개선
            questions = []
            for line in response_text.split('\n'):
                line = line.strip()
                if not line or len(line) < 5: continue
                
                # 불필요한 서두 제거
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                line = re.sub(r'^[-\*\+]\s*', '', line) 
                line = line.strip('"\' ')
                
                if '?' in line:
                    questions.append(line)
            
            logger.info(f"✅ AI 맞춤형 질문 생성 성공: {len(questions)}개")
            
            # 부족하면 fallback
            if len(questions) < count:
                logger.warning(f"생성된 질문이 부족함 ({len(questions)}/{count}). Fallback 추가.")
                questions.extend(self._get_fallback_questions(position, count - len(questions)))
            
            return questions[:count]
            
        except Exception as e:
            logger.error(f"질문 생성 중 오류: {e}")
            return self._get_fallback_questions(target_role, count)

    def generate_human_like_question(
        self,
        name: str,
        stage: str,
        guide: str,
        context_list: List[Dict]
    ) -> str:
        """베테랑 면접관 스타일의 단일 질문 생성 (RAG 기반)
        
        Args:
            name (str): 지원자 이름
            stage (str): 면접 단계 (예: 직무 지식 평가)
            guide (str): 평가 의도/가이드
            context_list (List[Dict]): RAG 검색 결과 리스트 [{'text': ...}, ...]
            
        Returns:
            str: 생성된 질문
        """
        if not context_list:
            return f"{name}님, 해당 직무에 지원하게 된 계기를 구체적으로 말씀해 주시겠습니까?"

        # 컨텍스트 텍스트 변환
        texts = [item['text'] for item in context_list] if isinstance(context_list[0], dict) else context_list
        context_text = "\n".join([f"- {txt}" for txt in texts])

        prompt_template = """[|system|]
너는 15년 차 베테랑 '보안 직무 면접관'이다. 
지금은 **면접이 한창 진행 중인 상황**이다. (자기소개는 이미 끝났다.)
제공된 [이력서 내용]을 근거로, 해당 단계({stage})에 맞는 **날카로운 질문 1개**만 던져라.

[작성 절대 금지 사항] 
1. **"자기소개 부탁드립니다" 절대 금지.** (이미 했다고 가정)
2. **"(잠시 침묵)", "답변 감사합니다"** 같은 가상의 지문이나 대본을 쓰지 마라.
3. 질문 앞뒤에 사족을 붙이지 말고 **질문만 깔끔하게** 출력하라.

[질문 스타일 가이드]
1. 시작은 반드시 **"{name}님,"** 으로 부르며 시작할 것.
2. **"이력서를 보니...", "자소서를 읽어보니 ~라고 하셨는데..."** 처럼 근거를 명확히 댈 것.
3. 말투는 정중하면서도 예리한 면접관 톤(..하셨는데, ..설명해 주시겠습니까?)을 유지할 것.
[|endofturn|]
[|user|]
# 평가 단계: {stage}
# 평가 의도: {guide}
# 지원자 이력서 근거:
{context}

# 요청:
위 내용을 바탕으로 {name} 지원자에게 **단도직입적으로** 질문을 던져줘.
[|endofturn|]
[|assistant|]"""

        prompt = prompt_template.format(
            name=name,
            stage=stage,
            guide=guide,
            context=context_text
        )

        try:
            output = self.llm(
                prompt,
                max_tokens=256,
                stop=["[|endofturn|]", "[|user|]"],
                temperature=0.7,
                top_p=0.9,
                echo=False
            )
            
            response_text = output['choices'][0]['text'].strip()
            # 혹시 모를 따옴표 제거
            response_text = response_text.strip('"\'')
            return response_text
            
        except Exception as e:
            logger.error(f"질문 생성 실패: {e}")
            return f"{name}님, 준비하신 내용을 바탕으로 편하게 말씀해 주십시오."

    def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        rubric: Optional[Dict] = None
    ) -> Dict:
        """답변 평가
        
        Args:
            question_text (str): 평가할 질문 텍스트
            answer_text (str): 평가할 답변 텍스트
            rubric (Optional[Dict], optional): 평가 기준. Defaults to None.
            
        Returns:
            Dict: 평가 결과
        
        생성자: ejm
        생성일자: 2026-02-04
        """
        if not answer_text or not answer_text.strip():
            return {"technical_score": 0, "communication_score": 0, "feedback": "답변이 없습니다."}

        system_msg = "당신은 공정하고 엄격한 면접관입니다. 지원자의 답변을 평가하여 JSON 형식으로 출력하세요."
        user_msg = f"""다음 면접 질문과 답변을 평가하세요.

질문: {question_text}
답변: {answer_text}

평가 기준:
1. 기술적 정확성 (1-5점)
2. 의사소통 능력 (1-5점)
3. 구체적인 피드백 (한국어)

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "technical_score": 3,
    "communication_score": 3,
    "feedback": "피드백 내용"
}}"""

        prompt = self._create_prompt(system_msg, user_msg)
        
        try:
            output = self.llm(
                prompt,
                max_tokens=512,
                stop=["[|endofturn|]"],
                temperature=0.1, # 일관된 평가를 위해 낮음
                echo=False
            )
            
            response_text = output['choices'][0]['text']
            
            # JSON 추출
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {
                        "technical_score": int(result.get("technical_score", 3)),
                        "communication_score": int(result.get("communication_score", 3)),
                        "feedback": result.get("feedback", "평가 완료")
                    }
                except:
                    pass
            
            # 파싱 실패 시
            logger.warning(f"JSON 파싱 실패. Raw response: {response_text}")
            return {"technical_score": 3, "communication_score": 3, "feedback": "평가 결과를 산출할 수 없습니다. (형식 오류)"}

        except Exception as e:
            logger.error(f"평가 중 오류: {e}")
            return {"technical_score": 3, "communication_score": 3, "feedback": "평가 중 시스템 오류 발생"}

    def _get_fallback_questions(self, target_role: str, count: int) -> List[str]:
        """기본 질문 생성
        
        Args:
            target_role (str): 직무 포지션
            count (int): 생성할 질문 수
            
        Returns:
            List[str]: 생성된 기본 질문 리스트
        
        생성자: ejm
        생성일자: 2026-02-07
        """
        base_qs = [
            f"{target_role} 직무에 지원하게 된 구체적인 동기는 무엇인가요?",
            "본인의 가장 큰 강점과 약점은 무엇이라고 생각하나요?",
            "입사 후 3년, 5년, 10년 후의 커리어 계획은 무엇인가요?",
            "동료와 의견 충돌이 발생했을 때 어떻게 대처하시나요?",
            "최근 관심 있게 보고 있는 기술 트렌드는 무엇인가요?"
        ]
        return base_qs[:count]

def get_exaone_llm() -> ExaoneLLM:
    """싱글톤 인스턴스 반환
    
    Returns:
        ExaoneLLM: 싱글톤 인스턴스
    
    생성자: ejm
    생성일자: 2026-02-07
    """
    return ExaoneLLM()

# [최적화] 모듈 임포트 시 즉시 로딩(Warmup) 제거. 
# 이제 각 워커가 실제 태스크를 수행할 때 필요에 따라 로드함.
