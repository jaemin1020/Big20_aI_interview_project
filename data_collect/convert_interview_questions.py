import json
import re

def convert_to_interview_style(question):
    """
    질문을 면접 형식으로 변환합니다.
    ~하라 -> ~해주시겠습니까?
    ~무엇인가 -> ~무엇인가요?
    """
    # 이미 면접 형식인 경우
    if question.endswith('까?') or question.endswith('습니까?') or question.endswith('나요?'):
        return question
    
    # "~하라" 패턴들
    conversions = {
        '설명하라': '설명해주시겠습니까?',
        '선택하라': '선택해주시겠습니까?',
    }
    
    for old, new in conversions.items():
        if question.endswith(old):
            return question[:-len(old)] + new
    
    # "무엇인가" -> "무엇인가요?"
    if question.endswith('무엇인가'):
        return question + '요?'
    
    # "~인가" -> "~인가요?"
    if question.endswith('인가'):
        return question + '요?'
    
    # 기타 "~점" 형식
    if question.endswith('차이점') or question.endswith('공통점'):
        return question + '은 무엇인가요?'
    
    # 기타 "~수" 형식  
    if question.endswith('횟수'):
        return question + '는 얼마인가요?'
    
    return question

def main():
    input_file = 'data_collect/final_interview_dataset_github_1.json'
    
    print(f"파일 읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"총 {len(data)}개의 질문을 변환합니다...\n")
    
    # 질문 변환
    converted_count = 0
    for i, item in enumerate(data, 1):
        original = item['질문']
        converted = convert_to_interview_style(original)
        
        if original != converted:
            converted_count += 1
            if converted_count <= 10:  # 처음 10개만 출력
                print(f"{i}. {original}")
                print(f"   → {converted}\n")
        
        item['질문'] = converted
    
    # 파일 저장
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\n{'='*50}")
    print(f"✅ 변환 완료!")
    print(f"총 {len(data)}개 중 {converted_count}개의 질문이 변경되었습니다.")
    print(f"저장 위치: {input_file}")

if __name__ == "__main__":
    main()
