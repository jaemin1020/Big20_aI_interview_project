
import os

def merge_markdown_files(base_path, output_filename):
    files = [
        "01-파싱.md",
        "02-청킹.md",
        "03.엑사원모델.md",
        "04.임베딩.md",
        "05.pgvector.md",
        "06.rag.md",
        "07.resume-embedding-orcas.md",
        "08-질문생성.md"
    ]
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        outfile.write("# 📑 AI-워커 엔진 진행 보고서 (통합본)\n\n")
        outfile.write("---\n\n")
        
        for filename in files:
            file_path = os.path.join(base_path, filename)
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
                
            outfile.write(f"## [{filename}]\n\n")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                outfile.write(content)
                outfile.write("\n\n---\n\n")
                
    return output_filename

if __name__ == "__main__":
    # Get the root directory of the project (parent of "scripts")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.join(project_root, "파이널_진행보고서", "ai-워커")
    target_file = os.path.join(project_root, "AI_Worker_Combined_Report_Final.md")
    try:
        merge_markdown_files(base_dir, target_file)
        print(f"Successfully merged: {target_file}")
    except Exception as e:
        print(f"Error: {e}")
