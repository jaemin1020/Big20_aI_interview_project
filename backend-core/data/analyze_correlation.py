
import json
import pandas as pd
import os

JSON_PATH = r"C:\big20\git\Big20_aI_interview_project\backend-core\data\preprocessed_data.json"

def main():
    if not os.path.exists(JSON_PATH):
        print(f"Error: File not found at {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Create crosstab
    crosstab = pd.crosstab(df['QuestionCategory'], df['QUESTION_TYPE'])

    print("\n[Cross-tabulation: QuestionCategory vs QUESTION_TYPE]")
    print(crosstab)

    # Also Check singular mappings to see if any category maps to multiple types
    print("\n[Mapping Analysis]")
    for cat in df['QuestionCategory'].unique():
        types = df[df['QuestionCategory'] == cat]['QUESTION_TYPE'].unique()
        print(f"{cat} maps to: {types}")

if __name__ == "__main__":
    main()
