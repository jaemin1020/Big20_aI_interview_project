import time
import json
import requests
from bs4 import BeautifulSoup
import re
import os

def main():
    base_url = "https://www.jobkorea.co.kr/recruit/joblist?menucode=duty&tab=all"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    log_f = open("crawler_debug.log", "w", encoding="utf-8")
    def log(msg):
        print(msg)
        try:
            log_f.write(str(msg) + "\n")
            log_f.flush()
        except:
            pass

    log(f"Fetching job list from: {base_url}")
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        log(f"Error fetching job list: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    job_links_set = set()
    job_links = []
    
    # Extract job detail links
    # Standard JobKorea links: /Recruit/GI_Read/[ID]
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/Recruit/GI_Read/' in href and 'GI_Read_View' not in href:
            full_url = "https://www.jobkorea.co.kr" + href if href.startswith('/') else href
            
            # Simple deduplication by extracting ID
            try:
                # Example: .../GI_Read/123456?rPageCode=...
                # Get the part after GI_Read/
                parts = full_url.split('/Recruit/GI_Read/')
                if len(parts) > 1:
                    job_id = parts[1].split('?')[0] # Remove query params
                    
                    if job_id and job_id not in job_links_set:
                        job_links_set.add(job_id)
                        job_links.append(full_url)
            except Exception:
                continue
                
        if len(job_links) >= 10:
            break
            
    log(f"Found {len(job_links)} unique job links.")
    
    results = []
    
    for i, link in enumerate(job_links):
        log(f"Processing ({i+1}/10): {link}")
        time.sleep(5)  # Compulsory 5s delay
        
        try:
            resp = requests.get(link, headers=headers)
            resp.raise_for_status()
            detail_soup = BeautifulSoup(resp.text, 'html.parser')
            
            job_data = {
                "url": link,
                "responsibilities": [], # 이런 업무를 해요
                "requirements": [],      # 이런 분들을 찾고 있어요
                "preferred": [],         # 이런 분이면 더 좋아요
                "tech_stack": []         # 이런 기술이 필요해요
            }
            
            # Iterate over all .detail-article elements matches the user's HTML structure
            articles = detail_soup.find_all('li', class_='detail-article')
            
            # Fallback: sometimes the structure might be slightly different or nested in a different way
            # The user's snippet specifically shows <li class="detail-article"> inside presumably a list
            # We search for the headers specifically.
            
            # If no articles found via the specific li class (maybe page structure varies),
            # try finding by header text directly.
            
            found_articles = False
            
            for article in articles:
                found_articles = True
                title_tag = article.find('h3', class_='title')
                if not title_tag:
                    continue
                
                title_text = title_tag.get_text(strip=True)
                
                content_list = []
                # Check for "sentence" class (general text) or "view-content-detail-skill" (skills)
                ul_sentence = article.find('ul', class_='sentence')
                ul_skill = article.find('ul', class_='view-content-detail-skill')
                
                target_ul = ul_sentence if ul_sentence else ul_skill
                
                if target_ul:
                    for li in target_ul.find_all('li'):
                        text = li.get_text(strip=True)
                        if text:
                            content_list.append(text)
                            
                # Map extracted content to our JSON keys
                if "이런 업무를 해요" in title_text:
                    job_data["responsibilities"] = content_list
                elif "이런 분들을 찾고 있어요" in title_text:
                    job_data["requirements"] = content_list
                elif "이런 분이면 더 좋아요" in title_text:
                    job_data["preferred"] = content_list
                elif "이런 기술이 필요해요" in title_text:
                    job_data["tech_stack"] = content_list
            
            # If the user's specific structure wasn't found (maybe different template for some jobs),
            # we simply return empty lists for that job or try a broader search.
            # For this task, we assume the structure matches the user's provided 'valid' structure for target jobs.
            
            results.append(job_data)
            
        except Exception as e:
            log(f"Failed to process {link}: {e}")
            
    # Save output to the same directory as the script
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobkorea_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        
    log(f"Done. Saved {len(results)} items to {output_path}")

if __name__ == "__main__":
    main()
