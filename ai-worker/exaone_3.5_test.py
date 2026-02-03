import json
import time
from typing import List, Dict, Optional
from llama_cpp import Llama

# ==================================================================================
# Exaone 3.5 테스트 모듈 (LlamaCpp 직접 사용)
# 로컬 GGUF 모델 사용: ai-worker/models/EXAONE-4.0-1.2B-BF16.gguf
# LangChain 의존성을 제거하고 가벼운 llama-cpp-python만 사용합니다.
# ==================================================================================

class ExaoneTestModule:
    def __init__(self, model_path: str = "/models/EXAONE-4.0-1.2B-BF16.gguf"):
        """
        LlamaCpp를 사용하여 로컬 GGUF 모델을 연결합니다.
        
        Args:
            model_path (str): .gguf 모델 파일의 경로.
        """
        self.model_path = model_path
        
        # LlamaCpp 모델 초기화 (GPU 가속을 끄고 CPU로 안전하게 실행)
        print(f"[Init] 모델 로딩 중...: {self.model_path}")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,      # 컨텍스트 윈도우 크기
            n_gpu_layers=0,  # CPU만 사용
            verbose=False    # 불필요한 로그 숨김
        )
        print(f"[ExaoneTestModule] 모델 초기화 완료")

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        llama-cpp-python을 직접 사용하여 답변을 생성합니다.
        """
        try:
            # 프롬프트 구성 (ChatML 포맷 혹은 단순 연결)
            # EXAONE이나 Llama 계열은 보통 시스템/유저 프롬프트를 명확히 구분하는 것이 좋습니다.
            full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
            
            print(f"\n>>> [생성 시작]")
            start_time = time.time()
            
            # 텍스트 생성 실행
            output = self.llm(
                full_prompt,
                max_tokens=1024,
                temperature=0.7,
                stop=["<|end|>", "</s>"], # 종료 토큰 설정
                echo=False # 입력 프롬프트는 출력에서 제외
            )
            
            response = output['choices'][0]['text'].strip()
            
            execution_time = time.time() - start_time
            print(f">>> [생성 완료] 소요 시간: {execution_time:.2f}초")
            
            return response

        except Exception as e:
            print(f"!! [오류] 모델 생성 중 에러 발생: {e}")
            return f"[오류] {str(e)}"

    def generate_questions_from_resume(self, resume_text: str, num_questions: int = 3) -> List[str]:
        """
        이력서 데이터를 기반으로 면접 질문을 생성합니다.
        """
        print("\n--- [1단계] 이력서 기반 질문 생성 ---")
        
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
        if not questions:
            questions = [response]
            
        return questions

    def evaluate_answer_with_rubric(self, question: str, answer: str, rubric_criteria: str) -> Dict:
        """
        질문과 답변을 루브릭 기준(JSON 포맷)으로 평가합니다.
        """
        print(f"\n--- [2단계] 답변 평가 ---")
        
        system_prompt = "당신은 공정한 채용 평가자입니다. 주어진 평가 기준(Rubric)에 따라 지원자의 답변을 분석하고 점수와 피드백을 제공하세요."
        
        user_prompt = f"""
[면접 질문]
{question}

[지원자 답변]
{answer}

[평가 기준(Rubric)]
{rubric_criteria}

위 답변을 평가하여 반드시 다음 JSON 형식으로만 응답하세요 (다른 말 덧붙이지 마세요):
{{
    "score": (0~100 사이 숫자),
    "feedback": "상세 피드백 내용",
    "pass": (true 또는 false)
}}
"""
        response = self.generate_response(system_prompt, user_prompt)
        
        # JSON 파싱 시도
        try:
            # Markdown 코드 블록 제거 및 정리
            clean_response = response.replace("```json", "").replace("```", "").strip()
            # JSON 시작과 끝 부분만 추출 시도 (간단한 파싱 보정)
            if "{" in clean_response and "}" in clean_response:
                start = clean_response.find("{")
                end = clean_response.rfind("}") + 1
                clean_response = clean_response[start:end]
                
            return json.loads(clean_response)
        except json.JSONDecodeError:
            print(f"!! JSON 파싱 실패 (원본 텍스트 반환): {response}")
            return {"raw_response": response}

# ==================================================================================
# 실행 블록
# ==================================================================================
if __name__ == "__main__":
    # 1. 모델 연결 테스트
    tester = ExaoneTestModule()
    
    # 2. 테스트 데이터
    resume = "이름: 김개발\n직무: 파이썬 백엔드\n경력: 대규모 트래픽 처리 경험, Redis 캐싱 전략 수립."
    rubric = "구체적인 기술 용어 사용 여부와 문제 해결 과정을 논리적으로 설명하는지 평가."
    
    # 3. 질문 생성 실행
    qs = tester.generate_questions_from_resume(resume)
    print("생성된 질문들:", qs)
    
    # 4. 평가 실행 (첫 번째 질문에 대해)
    if qs:
        target_q = qs[0]
        ans = "Redis의 Eviction Policy를 활용하여 메모리 효율을 높였습니다."
        
        eval_res = tester.evaluate_answer_with_rubric(target_q, ans, rubric)
        print("평가 결과:", eval_res)
