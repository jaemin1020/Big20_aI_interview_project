import json

def main():
    input_file = 'data_collect/final_interview_dataset_github_2.json'
    
    print(f"파일 읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"총 {len(data)}개의 답변에서 줄바꿈을 제거합니다...\n")
    
    # 답변에서 \n 제거
    modified_count = 0
    for i, item in enumerate(data, 1):
        original_answer = item['답변']
        
        if '\n' in original_answer:
            # \n을 공백으로 대체
            cleaned_answer = original_answer.replace('\n', ' ')
            # 중복 공백 제거
            cleaned_answer = ' '.join(cleaned_answer.split())
            
            item['답변'] = cleaned_answer
            modified_count += 1
            
            if modified_count <= 5:  # 처음 5개만 출력
                print(f"{i}번째 답변 변경:")
                print(f"  원본: {original_answer[:80]}...")
                print(f"  변경: {cleaned_answer[:80]}...")
                print()
    
    # 파일 저장
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"{'='*50}")
    print(f"✅ 완료!")
    print(f"총 {len(data)}개 중 {modified_count}개의 답변이 수정되었습니다.")
    print(f"저장 위치: {input_file}")

if __name__ == "__main__":
    main()
