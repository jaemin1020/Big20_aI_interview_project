
import json
import os
from collections import Counter

JSON_PATH = r"C:\big20\git\Big20_aI_interview_project\backend-core\data\preprocessed_data.json"

def main():
    if not os.path.exists(JSON_PATH):
        print(f"Error: File not found at {JSON_PATH}")
        return

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    total_count = len(data)
    print(f"총 데이터 개수: {total_count:,}건")

    # Fields to analyze
    fields = [
        ("QuestionCategory", "카테고리별 분포"),
        ("QuestionDifficulty", "난이도별 분포"),
        ("QUESTION_TYPE", "질문 유형별 분포")
    ]

    for field_key, title in fields:
        print(f"\n{title}:")
        # Extract values, handling missing keys gracefully (though previous checks suggest they exist)
        values = [item.get(field_key, "Unknown/Missing") for item in data]
        counts = Counter(values)

        # Sort by count descending
        sorted_counts = counts.most_common()

        for value, count in sorted_counts:
            percentage = (count / total_count) * 100
            print(f"  - {value}: {count:,}건 ({percentage:.1f}%)")

if __name__ == "__main__":
    main()
