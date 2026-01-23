import requests
import json
import re
import os
import time
from requests.utils import quote

def get_job_interview_data(username, repo, branch, file_list):
    all_data = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 한글 폴더명 '직무' 인코딩
    job_folder = quote("직무")

    for file_name in file_list:
        # 4z7l 저장소의 실제 파일명은 소문자입니다. (예: cpp.md)
        target_file = file_name.lower()
        raw_url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}/{job_folder}/{target_file}.md"
        
        print(f"[{file_name}] 수집 시도 중: {raw_url}")
        
        try:
            response = requests.get(raw_url, headers=headers)
            
            if response.status_code != 200:
                print(f"   => 실패: 404 에러. 브랜치나 파일명을 다시 확인하세요.")
                continue
            
            content = response.text
            
            # <details> 구조 내 질문(summary strong)과 답변(p) 추출
            pattern = re.compile(
                r'<summary>.*?<strong>(.*?)</strong>.*?</summary>.*?<p.*?>(.*?)</p>', 
                re.DOTALL | re.IGNORECASE
            )
            matches = pattern.findall(content)
            
            print(f"   => 성공: {len(matches)}개 문답 발견")

            for q, a in matches:
                clean_q = re.sub(r'<.*?>', '', q).strip()
                clean_a = re.sub(r'<.*?>', '', a).strip()
                
                if clean_q and clean_a:
                    all_data.append({
                        "질문": clean_q,
                        "답변": clean_a
                    })
            
            time.sleep(0.5)

        except Exception as e:
            print(f"   => 에러 발생: {e}")
            
    return all_data

if __name__ == "__main__":
    # 404 해결을 위한 핵심 설정 변경
    USER = "4z7l"
    REPO = "tech_interview"
    BRANCH = "master" # main에서 master로 변경
    
    # 실제 저장소 파일명 기반 리스트
    TARGET_FILES = [
        'cpp', 'java', 'kotlin', 'algorithm', 
        'datastructure', 'database', 'network', 
        'os', 'softwareengineering', 'android', 
        'frontend', 'rxjava', 'git'
    ]

    final_list = get_job_interview_data(USER, REPO, BRANCH, TARGET_FILES)

    folder_path = 'data_collect'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    save_path = os.path.join(folder_path, 'final_tech_interview_dataset.json')

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=4)

    print("\n" + "="*40)
    print(f"최종 수집 완료: {len(final_list)}개")
    print(f"파일 저장 경로: {os.path.abspath(save_path)}")