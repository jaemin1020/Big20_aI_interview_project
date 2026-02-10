import subprocess
import os
import re
import requests
import json
import time

# --- Configuration ---
LOG_FILE_NAME = "DEVELOPMENT_LOG.md"
OLLAMA_MODEL = "exaone3.5:latest" 
OLLAMA_API_URL = "http://localhost:11434/api/generate"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, LOG_FILE_NAME)

def run_git_cmd(cmd):
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"Error running git command: {cmd}\n{result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception running git command: {e}")
        return None

def get_recent_commits(limit=10):
    cmd = ['git', 'log', '--pretty=format:%H', '-n', str(limit)]
    output = run_git_cmd(cmd)
    if not output: return []
    commits = output.split('\n')
    return commits

def get_commit_details(commit_hash):
    cmd_meta = ['git', 'show', '--format=%H|#|%an|#|%ad|#|%s', '--date=short', '--no-patch', commit_hash]
    meta_out = run_git_cmd(cmd_meta)
    if not meta_out: return None
    
    parts = meta_out.split('|#|')
    if len(parts) < 4: return None
    
    metadata = {
        'hash': parts[0],
        'author': parts[1],
        'date': parts[2],
        'message': parts[3]
    }

    cmd_files = ['git', 'show', '--name-only', '--format=', commit_hash]
    files_out = run_git_cmd(cmd_files)
    files = [f for f in files_out.split('\n') if f.strip()] if files_out else []
    metadata['files'] = files

    cmd_diff = ['git', 'show', '--format=', commit_hash]
    diff_out = run_git_cmd(cmd_diff)
    metadata['diff'] = diff_out[:4000] if diff_out else "" 
    return metadata

def analyze_commit_with_llm(commit_data):
    diff_snippet = commit_data['diff']
    message = commit_data['message']
    
    if not diff_snippet.strip():
        # Heuristic for merge/empty
        prompt = f"""
        Analyze this git commit message: '{message}'.
        Respond STRICTLY with a valid JSON using Korean.
        Keys: "category" (Short tag), "cause", "before", "after", "content".
        """
    else:
        prompt = f"""
        Analyze this git commit.
        Commit Message: {message}
        Diff (truncated):
        {diff_snippet}
        
        Respond STRICTLY with a valid JSON object.
        Keys:
        - "category": A very short keyword (e.g., 'DB수정', '버그픽스').
        - "cause": Reason for change.
        - "before": State before change.
        - "after": State after change.
        - "content": Detailed summary.
        
        Language: Korean.
        JSON only.
        """
    
    try:
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"}
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=90)
        if response.status_code == 200:
            result = response.json()
            data = json.loads(result.get('response', '{}'))
            return {
                'category': data.get('category', 'Update'),
                'cause': data.get('cause', '분석 불가'),
                'before': data.get('before', '-'),
                'after': data.get('after', '-'),
                'content': data.get('content', message)
            }
        return None
    except Exception:
        return None

def main():
    print(f"Updating Log: {LOG_FILE_PATH}")
    
    # Read existing
    current_content = ""
    if os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            current_content = f.read()

    # Detect if we need to switch from Table -> Block format
    # precise check: if it starts with | and not #, it's a table
    is_table_format = "|" in current_content[:100] if current_content else False
    
    if is_table_format:
        print("Table format detected. Converting to List format... (Starting fresh for recent items)")
        current_content = ""
    
    processed_hashes = set(re.findall(r'<!-- hash:([a-f0-9]+) -->', current_content))
    
    # Get recent 10 commits
    recent_hashes = get_recent_commits(10)
    to_process = [h for h in recent_hashes if h not in processed_hashes]
    
    if not to_process:
        print("No new commits.")
        return

    print(f"Processing {len(to_process)} commits...")
    new_blocks = []
    
    for h in to_process:
        print(f" - {h[:7]}...")
        data = get_commit_details(h)
        if not data: continue
        
        analysis = analyze_commit_with_llm(data)
        if not analysis:
            analysis = {'category': 'Check', 'cause': 'LLM Error', 'before': '-', 'after': '-', 'content': data['message']}
            
        # Format as Block
        # ---------------------------------------------------------
        # ## [Commit ID] YYYY-MM-DD (Author)
        #
        # **[Category] Cause Summary**
        # 
        # - **위치**: 
        #   - file1
        #   - file2...
        # - **수정 원인**: ...
        # - **개선 전 (Before)**: ...
        # - **개선 후 (After)**: ...
        # - **상세 변경 내용**: ...
        # <!-- hash:xxx -->
        # ---------------------------------------------------------
        
        file_list_str = "\n  - " + "\n  - ".join(data['files'][:10]) # limit 10 files
        if len(data['files']) > 10: file_list_str += f"\n  - ... (+{len(data['files'])-10} more)"
        if not data['files']: file_list_str = "  - (No file changes detected)"
            
        block = f"""
## [{data['hash'][:7]}] {data['date']} (작성자: {data['author']})

**[{analysis['category']}] {analysis['cause']}**

- **수정 위치**: {file_list_str}
- **수정 원인**: {analysis['cause']}
- **개선 전 (Before)**:
  > {analysis['before']}
- **개선 후 (After)**:
  > {analysis['after']}
- **상세 변경 내용**:
  {analysis['content']}

<!-- hash:{data['hash']} -->
---
"""
        new_blocks.append(block)

    if not new_blocks: return

    # For block format, we want Newest at the top (usually). 
    # Current content (if any) should be appended after new blocks.
    
    header = "# 📝 Development Change Log\n\n"
    
    if not current_content:
        final_content = header + "".join(new_blocks)
    else:
        # If content exists, insert after header? or just prepend to existing entries?
        # If header exists
        if current_content.startswith("# "):
            lines = current_content.splitlines()
            # Find where entries start (after header and maybe a separator)
            # Just append after lines[2] if generic standard? 
            # Safest: Insert after the first header line or empty lines
            final_content = header + "".join(new_blocks) + "\n" + current_content.replace(header.strip(), "").strip()
        else:
            final_content = header + "".join(new_blocks) + "\n" + current_content

    with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print("Done.")

if __name__ == "__main__":
    main()
