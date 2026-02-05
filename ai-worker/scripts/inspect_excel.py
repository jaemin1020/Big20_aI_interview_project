
import pandas as pd
import os

file_path = 'scripts/llm_test_data.xlsx'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
else:
    try:
        df = pd.read_excel(file_path)
        print("Columns:", df.columns.tolist())
        print("First row:", df.iloc[0].to_dict())
    except Exception as e:
        print(f"Error reading excel: {e}")
