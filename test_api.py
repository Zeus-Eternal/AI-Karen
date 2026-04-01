import requests
import json
import os

API_URL = "http://localhost:8000/api/conversations"

# Try with no auth first
try:
    print(f"Testing {API_URL}...")
    response = requests.get(API_URL)
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response body: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
