# 1단계: 필요한 라이브러리 및 모듈 불러오기
import os  # 파일 및 경로 조작을 위한 모듈
import json  # 결과 저장을 위한 JSON 모듈
import argparse  # 커맨드라인 인자 파싱을 위한 모듈
from datetime import datetime  # 현재 시간 측정을 위한 datetime 모듈
import sys

# 상위 디렉토리를 시스템 경로에 추가 (모듈 임포트 문제 해결)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 우리가 분리해서 만든 모델 파일들을 각각 불러옵니다.
from stt_poc.whisper_v3_turbo import WhisperTurboSTT  # Whisper 모델
from stt_poc.nova_1 import Nova1STT                   # Nova-1 모델 (Placeholder)
from stt_poc.nova_2 import Nova2STT                   # Nova-2 모델 (Placeholder)

from stt_poc.scenarios import SCENARIOS, Scenario     # 테스트할 시나리오들
from stt_poc.evaluator import calculate_wer, calculate_cer, analyze_results # 평가 로직

# 2단계: 데이터 저장소 경로 설정
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# 3단계: 단일 시나리오 실행 함수 정의
def run_scenario_iteration(model, scenario: Scenario, iteration: int):
    """
    하나의 모델로 하나의 시나리오를 1회 실행하는 함수입니다.
    """
    # 3-1: 오디오 파일 경로 확인
    audio_path = os.path.join(DATA_DIR, scenario.audio_file)
    
    if not os.path.exists(audio_path):
        # 파일이 없으면 즉시 에러 반환
        print(f"[경고] 오디오 파일을 찾을 수 없습니다: {audio_path}")
        return {
            "model": model.model_name,
            "scenario": scenario.name,
            "iteration": iteration,
            "success": False,
            "error": "파일이 없습니다 (File not found)"
        }

    # 3-2: 모델에게 음성 인식을 시킵니다 (Transcribe)
    result = model.transcribe(audio_path)
    
    # 3-3: 결과 확인 (에러가 있으면 실패 처리)
    if result['error']:
        return {
            "model": model.model_name,
            "scenario": scenario.name,
            "iteration": iteration,
            "success": False,
            "error": result['error'],
            "latency": result['latency']
        }

    # 3-4: 평가 지표 계산 (WER, CER) - 정답지(Ground Truth)와 비교
    wer = calculate_wer(scenario.ground_truth, result['text'])
    cer = calculate_cer(scenario.ground_truth, result['text'])
    
    # 3-5: 성공 결과 반환
    return {
        "model": model.model_name,
        "scenario": scenario.name,
        "iteration": iteration,
        "success": True,
        "text": result['text'], 
        "latency": result['latency'], 
        "wer": wer, 
        "cer": cer 
    }

# 4단계: 메인 실행 흐름 정의
def main():
    # 4-1: 실행 옵션 설정 (어떤 모델을 돌릴지, 몇 번 반복할지)
    parser = argparse.ArgumentParser(description="STT POC 검증 실행")
    
    # 기본값으로 'whisper-v3-turbo'만 실행하도록 설정했습니다.
    parser.add_argument("--models", nargs="+", default=["whisper-v3-turbo"], 
                        help="실행할 모델 목록 (예: whisper-v3-turbo nova-1 nova-2)")
    parser.add_argument("--iterations", type=int, default=5, 
                        help="시나리오별 반복 횟수 (기본값: 5)")
    args = parser.parse_args()

    # 4-2: 선택된 모델 초기화(로딩)
    models = []
    
    # Whisper 모델 추가
    if "whisper-v3-turbo" in args.models:
        # GPU 사용 가능 여부 확인
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
            
        models.append(WhisperTurboSTT("large-v3", config={"device": device})) 
    
    # Nova-1 모델 추가 (지금은 Placeholder)
    if "nova-1" in args.models:
        models.append(Nova1STT("nova-1"))
    
    # Nova-2 모델 추가 (지금은 Placeholder)
    if "nova-2" in args.models:
        models.append(Nova2STT("nova-2"))

    all_results = [] # 결과를 모을 리스트
    
    print(f"\n[시작] POC 검증을 시작합니다. 시간: {datetime.now()}")
    print(f"[설정] 대상 모델: {[m.model_name for m in models]}")
    print(f"[설정] 반복 횟수: {args.iterations}")

    # 4-3: 본격적인 테스트 루프 (모델 -> 시나리오 -> 반복)
    for model in models:
        print(f"\n--- [모델 테스트] {model.model_name} ---")
        
        for scenario in SCENARIOS:
            print(f"  > 시나리오: {scenario.name} ({scenario.description})")
            
            for i in range(1, args.iterations + 1):
                # 테스트 실행
                res = run_scenario_iteration(model, scenario, i)
                all_results.append(res)
                
                # 결과 한 줄 출력
                status = "성공" if res['success'] else f"실패 ({res.get('error')})"
                wer_score = res.get('wer', 0)
                latency = res.get('latency', 0)
                print(f"    반복 {i}: {status} | 시간: {latency:.4f}초 | WER: {wer_score:.4f}")

    # 5단계: 결과 종합 및 저장
    report = {}
    for model_name in [m.model_name for m in models]:
        report[model_name] = {}
        for scenario in SCENARIOS:
            # 해당 모델/시나리오 결과만 필터링
            subset = [r for r in all_results if r['model'] == model_name and r['scenario'] == scenario.name]
            # 통계 분석 (평균 등 계산)
            stats = analyze_results(subset)
            report[model_name][scenario.name] = stats

    # 6단계: JSON 파일로 저장
    output_file = f"stt_poc_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"raw": all_results, "summary": report}, f, indent=4, ensure_ascii=False)
    
    print(f"\n[완료] 검증이 끝났습니다.")
    print(f"[저장] 결과 파일: {output_file}")
    print(f"[안내] 'ai-worker/stt_poc/data' 폴더에 wav 5개가 제대로 들어있는지 꼭 확인하세요!")

if __name__ == "__main__":
    main()
