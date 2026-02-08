import os
import json
import time
from typing import List, Dict, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ==================================================================================
# Exaone 3.5 Mini (Ollama) 테스트 모듈
# 기존에 설치된 Ollama의 'exaone3.5' 모델을 사용합니다.
# ==================================================================================

class ExaoneTestModule:
    def __init__(self, model_name: str = "exaone3.5:latest", base_url: str = None):
        """
        Ollama를 통해 실행 중인 로컬 모델을 연결합니다.
        Docker 환경 지원을 위해 base_url을 설정합니다.
        
        Args:
            model_name (str): Ollama에 등록된 모델명
            base_url (str): Ollama 서버 주소 (None일 경우 환경 변수 또는 localhost 사용)
        """
        self.model_name = model_name
        
        # 로컬 환경에서는 localhost, Docker 내부에서 호스트의 Ollama에 접속하려면 'http://host.docker.internal:11434' 필요
        # 기본값을 http://localhost:11434로 변경하여 로컬 테스트를 원활하게 함
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        print(f"[Init] Ollama 연결 시도: {self.base_url} (Model: {self.model_name})")

        self.llm = ChatOllama(
            model=model_name,
            base_url=self.base_url,
            temperature=0.7, 
            max_tokens=1024
        )
        print(f"[ExaoneTestModule] 초기화 완료")

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        LangChain + Ollama를 사용하여 답변을 생성합니다.
        """
        try:
            # 프롬프트 템플릿 구성
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt)
            ])
            
            # 체인 연결: 프롬프트 -> 모델 -> 문자열 파서
            chain = prompt | self.llm | StrOutputParser()
            
            print(f"\n>>> [생성 시작] (모델: {self.model_name})")
            start_time = time.time()
            
            # 실행
            response = chain.invoke({}) 
            
            execution_time = time.time() - start_time
            print(f">>> [생성 완료] 소요 시간: {execution_time:.2f}초")
            
            return response.strip()

        except Exception as e:
            print(f"!! [오류] 모델 생성 중 에러 발생: {e}")
            return f"[오류] {str(e)}"

    def generate_questions_from_resume(self, resume_text: str, num_questions: int = 3) -> List[str]:
        """
        이력서 데이터를 기반으로 면접 질문을 생성합니다.
        """
        print("\n--- [1단계] 이력서 기반 질문 생성 ---")
        
        # ==========================================================================
        # [수정 필요 ✏️] 🔽 여기서 프롬프트를 변경하여 질문 스타일을 바꾸세요!
        # ==========================================================================
        system_prompt = "당신은 전문 면접관입니다. 지원자의 이력서를 분석하여 핵심 역량을 검증할 수 있는 날카로운 기술 면접 질문을 생성하세요."
        
        user_prompt = f"""
다음은 지원자의 이력서 내용입니다:
{resume_text}

위 내용을 바탕으로 기술 질문 {num_questions}개를 생성해주세요.
형식은 반드시 번호를 매겨서 나열해주세요. (예: 1. 질문내용)
"""

        response = self.generate_response(system_prompt, user_prompt)
        
        # 줄바꿈 기준으로 나누거나 번호 패턴을 찾아 리스트화
        questions = [q.strip() for q in response.split('\n') if q.strip() and (q[0].isdigit() or q.startswith('-'))]
        # 만약 파싱이 잘 안되면 통째로 반환
        if not questions:
            questions = [response]
            
        return questions

    def evaluate_answer_with_rubric(self, question: str, answer: str, rubric_criteria: str) -> Dict:
        """
        질문과 답변을 루브릭 기준(JSON 포맷)으로 평가합니다.
        """
        print(f"\n--- [2단계] 답변 평가 ---")
        
        # ==========================================================================
        # [수정 필요 ✏️] 🔽 여기서 프롬프트를 변경하여 평가 기준을 바꾸세요!
        # ==========================================================================
        system_prompt = "당신은 공정한 채용 평가자입니다. 주어진 평가 기준(Rubric)에 따라 지원자의 답변을 분석하고 점수와 피드백을 제공하세요."
        
        user_prompt = f"""
[면접 질문]
{question}

[지원자 답변]
{answer}

[평가 기준(Rubric)]
{rubric_criteria}

위 답변을 평가하여 반드시 다음 JSON 형식으로만 응답하세요 (다른 말 덧붙이지 마세요):
{{{{
    "score": (0~100 사이 숫자),
    "feedback": "상세 피드백 내용",
    "pass": (true 또는 false)
}}}}
"""
        response = self.generate_response(system_prompt, user_prompt)
        
        # JSON 파싱 시도
        try:
            # Markdown 코드 블록(```json ... ```) 제거
            clean_response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_response)
        except json.JSONDecodeError:
            print(f"!! JSON 파싱 실패 (원본 텍스트 반환): {response}")
            return {"raw_response": response}

# ==================================================================================
# 실행 블록
# ==================================================================================
if __name__ == "__main__":
    # 1. Ollama 연결 테스트
    # 사용자의 시스템에 'exaone3.5' 모델이 이미 설치되어 있다고 가정합니다.
    tester = ExaoneTestModule(model_name="exaone3.5")
    
    # 2. 테스트 데이터
    resume = "이름: 김개발\n직무: 파이썬 백엔드\n경력: 대규모 트래픽 처리 경험, Redis 캐싱 전략 수립."
    rubric = "구체적인 기술 용어 사용 여부와 문제 해결 과정을 논리적으로 설명하는지 평가."
    
    # 3. 질문 생성 실행
    qs = tester.generate_questions_from_resume(resume)
    print("생성된 질문들:", qs)
    
    # 4. 평가 실행 (첫 번째 질문에 대해)
    if qs:
        # 생성된 첫 번째 질문 사용
        target_q = qs[0]
        ans = "Redis의 Eviction Policy를 활용하여 메모리 효율을 높였습니다."
        
        eval_res = tester.evaluate_answer_with_rubric(target_q, ans, rubric)
        print("평가 결과:", eval_res)
