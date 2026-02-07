import json
import os

file_paths = [
    r"data_collect\final_interview_dataset_github_1.json",
    r"data_collect\final_interview_dataset_github_2.json",
    r"data_collect\interview.json"
]

total_count = 0
print("파일별 질문 개수:")

for file_path in file_paths:
    full_path = os.path.join(r"c:\big20\llm_agent", file_path)
    try:
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = len(data)
                print(f"- {file_path}: {count}개")
                total_count += count
        else:
            print(f"- {file_path}: 파일 없음")
    except Exception as e:
        print(f"- {file_path}: 읽기 오류 ({e})")

print(f"\n총 합계: {total_count}개")
