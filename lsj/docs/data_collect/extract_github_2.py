import os
import json
import glob
from bs4 import BeautifulSoup

def extract_qa_from_md(file_path):
    qa_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        soup = BeautifulSoup(content, 'html.parser')
        details_tags = soup.find_all('details')
        
        print(f"[{os.path.basename(file_path)}] found {len(details_tags)} details tags")
        
        for detail in details_tags:
            # Question extraction
            summary = detail.find('summary')
            if not summary:
                continue
                
            question = summary.get_text(strip=True)
            
            # Answer extraction
            # We want the content of details MINUS the summary
            # We can iterate over children and skip summary
            
            # Helper to get text from non-summary elements
            answer_parts = []
            for child in detail.children:
                if child.name == 'summary':
                    continue
                # Skip <hr> tags if they are just separators
                if child.name == 'hr':
                    continue
                    
                text = child.get_text(separator=" ", strip=True)
                if text:
                    answer_parts.append(text)
            
            answer = "\n".join(answer_parts).strip()
            
            if question and answer:
                qa_list.append({
                    "질문": question,
                    "답변": answer
                })
                
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        
    return qa_list

def main():
    target_dir = r"c:\big20\llm_agent\tech_interview.zip-main\직무"
    output_dir = r"c:\big20\llm_agent\data_collect"
    output_file = os.path.join(output_dir, "final_interview_dataset_github_2.json")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    md_files = glob.glob(os.path.join(target_dir, "*.md"))
    print(f"Found {len(md_files)} md files in {target_dir}")
    
    all_data = []
    for md_file in md_files:
        qa_data = extract_qa_from_md(md_file)
        all_data.extend(qa_data)
        
    print(f"Total extracted QA pairs: {len(all_data)}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
        
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
