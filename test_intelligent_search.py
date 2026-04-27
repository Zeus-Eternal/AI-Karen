
import requests
import json

def test_intelligent_search():
    url = "http://localhost:8000/api/plugins/intelligent-search/execute"
    headers = {
        "Content-Type": "application/json",
        "X-Skip-Auth": "dev",
        "X-Development-Mode": "true",
        "X-Mock-User-ID": "test-admin"
    }
    payload = {
        "plugin_name": "intelligent-search",
        "parameters": {
            "query": "latest news",
            "mode": "general"
        }
    }
    
    try:
        print(f"Calling {url}...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response success: {result.get('success')}")
        
        inner_result = result.get('result', {})
        sources = inner_result.get('sources', [])
        print(f"Sources found: {len(sources)}")
        
        if sources:
            for i, source in enumerate(sources[:2]):
                print(f"Source {i+1}: {source.get('title')} ({source.get('url')})")
        else:
            print("NO SOURCES RETURNED")
            if 'error' in inner_result:
                print(f"Error in result: {inner_result['error']}")
            if 'live_search_error' in inner_result:
                print(f"Live search error: {inner_result['live_search_error']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_intelligent_search()
