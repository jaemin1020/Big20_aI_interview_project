
import json
import os
import glob

# Paths
JSON_PATH = r"C:\big20\git\Big20_aI_interview_project\backend-core\data\preprocessed_data.json"
SCRIPTS_DATA_DIR = r"C:\big20\git\Big20_aI_interview_project\ai-worker\scripts\scripts_data"

def analyze_json():
    print("--- JSON Analysis ---")
    if not os.path.exists(JSON_PATH):
        print("JSON file not found.")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_count = len(data)
    print(f"Total entries: {total_count}")

    categories = {}
    difficulties = {}

    for item in data:
        cat = item.get('QuestionCategory', 'Unknown')
        diff = item.get('QuestionDifficulty', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
        difficulties[diff] = difficulties.get(diff, 0) + 1

    print(f"Category Distribution: {categories}")
    print(f"Difficulty Distribution: {difficulties}")
    print(f"Sample Item keys: {list(data[0].keys())}")
    print("---------------------")

def read_md_files():
    print("--- MD Files Summary ---")
    md_files = ["2차.md", "3차.md", "4차.md"]
    for md in md_files:
        path = os.path.join(SCRIPTS_DATA_DIR, md)
        if os.path.exists(path):
            print(f"Reading {md}...")
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Print first 200 chars or summary headers
                print(content[:500])
                print("...\n")

if __name__ == "__main__":
    analyze_json()
    read_md_files()
