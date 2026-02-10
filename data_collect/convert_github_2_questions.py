import json
import re

def convert_to_interview_style(question):
    """
    질문을 면접 형식으로 변환합니다.
    """
    # 이미 면접 형식인 경우
    if question.endswith('까?') or question.endswith('습니까?') or question.endswith('나요?') or question.endswith('세요?'):
        return question
    
    # "~하라" 형식
    if question.endswith('설명하라'):
        return question[:-4] + '설명해주시겠습니까?'
    if question.endswith('설명하라.'):
        return question[:-5] + '설명해주시겠습니까?'
    
    # 기타 "~하라" 패턴
    patterns = [
        (r'(.+)를 설명하라$', r'\1를 설명해주시겠습니까?'),
        (r'(.+)을 설명하라$', r'\1을 설명해주시겠습니까?'),
        (r'(.+)에 대해서 설명하라$', r'\1에 대해서 설명해주시겠습니까?'),
        (r'(.+)에 대해 설명하라$', r'\1에 대해 설명해주시겠습니까?'),
        (r'(.+)의 차이를 설명하라$', r'\1의 차이를 설명해주시겠습니까?'),
        (r'(.+) 설명하시오$', r'\1 설명해주시겠습니까?'),
    ]
    
    for pattern, replacement in patterns:
        if re.match(pattern, question):
            return re.sub(pattern, replacement, question)
    
    # "무엇인가" -> "무엇인가요?"
    if question.endswith('무엇인가'):
        return question + '요?'
    
    # "~인가" -> "~인가요?"
    if question.endswith('인가') and not question.endswith('무엇인가'):
        return question + '요?'
    
    # "~란" -> "~란 무엇인가요?"
    if question.endswith('란'):
        return question + ' 무엇인가요?'
    
    # 종결어미가 없는 경우 "~은 무엇인가요?" or "에 대해 설명해주시겠습니까?" 추가
    if not question.endswith('?') and not question.endswith('.'):
        # "차이" 또는 "종류" 등으로 끝나는 경우
        if any(question.endswith(word) for word in ['차이', '종류', '이유', '목적', '장점', '단점', '특징']):
            return question + '는 무엇인가요?'
        # 명사로 끝나는 경우
        return question + '에 대해 설명해주시겠습니까?'
    
    return question

def clean_escape_sequences(text):
    """
    이스케이프 시퀀스를 실제 형식으로 변환합니다.
    """
    if not text:
        return text
    
    # \n을 실제 줄바꿈으로 변경
    text = text.replace('\\n', '\n')
    
    # \r 제거
    text = text.replace('\\r', '')
    
    # \t를 공백으로
    text = text.replace('\\t', '    ')
    
    return text

def main():
    input_file = 'data_collect/final_interview_dataset_github_2.json'
    
    print(f"파일 읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"총 {len(data)}개의 질문을 변환합니다...\n")
    
    # 질문 변환 및 이스케이프 시퀀스 제거
    converted_count = 0
    for i, item in enumerate(data, 1):
        original_q = item['질문']
        original_a = item['답변']
        
        # 질문 변환
        converted_q = convert_to_interview_style(original_q)
        
        # 이스케이프 시퀀스 제거
        clean_q = clean_escape_sequences(converted_q)
        clean_a = clean_escape_sequences(original_a)
        
        if original_q != converted_q:
            converted_count += 1
            if converted_count <= 10:  # 처음 10개만 출력
                print(f"{i}. {original_q}")
                print(f"   → {converted_q}\n")
        
        item['질문'] = clean_q
        item['답변'] = clean_a
    
    # 파일 저장 (ensure_ascii=False로 한글 그대로 저장)
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\n{'='*50}")
    print(f"✅ 변환 완료!")
    print(f"총 {len(data)}개 중 {converted_count}개의 질문이 변경되었습니다.")
    print(f"이스케이프 시퀀스도 모두 제거되었습니다.")
    print(f"저장 위치: {input_file}")

if __name__ == "__main__":
    main()
