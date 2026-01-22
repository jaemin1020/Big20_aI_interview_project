from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults
import json

def search_samsung_ai_news_langchain():
    print("LangChain DuckDuckGo Wrapper를 사용하여 삼성전자 AI 관련 뉴스 검색 시작...")

    # DuckDuckGoSearchAPIWrapper 초기화
    # region="kr-kr": 한국
    # safe_search="moderate": 안전 검색 (옵션)
    # max_results=10
    wrapper = DuckDuckGoSearchAPIWrapper(
        region="kr-kr",
        max_results=10,
        backend="news" # 뉴스 검색 모드
    )

    # Tool 생성
    search_tool = DuckDuckGoSearchResults(api_wrapper=wrapper, backend="news")

    query = "삼성전자 AI 채용"
    
    try:
        # 검색 실행
        results_str = search_tool.run(query)
        
        print("\n--- 검색 결과 ---")
        print(results_str)
        
        output_file = "samsung_ai_news_langchain.json"
        
        # 결과 저장
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(results_str)
            
        print(f"\n검색 결과를 '{output_file}'에 저장했습니다.")

    except ImportError as e:
        print(f"\n[설치 오류] 필수 라이브러리가 누락되었습니다: {e}")
        print("해결 방법: pip install -U duckduckgo-search langchain-community")
    except Exception as e:
        print(f"\n[실행 오류] {e}")

if __name__ == "__main__":
    search_samsung_ai_news_langchain()
