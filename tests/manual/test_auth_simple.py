
import requests
import json

def test_dev_login():
    """Test the dev login endpoint"""
    try:
        response = requests.post("http://localhost:8000/api/auth/dev-login")
        if response.status_code == 200:
            data = response.json()
            print("✅ Dev login successful!")
            print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"   User: {data.get('user', {}).get('email', 'N/A')}")
            return data.get('access_token')
        else:
            print(f"❌ Dev login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Dev login error: {e}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint with the token"""
    if not token:
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8000/api/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Protected endpoint access successful!")
            print(f"   User info: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")

if __name__ == "__main__":
    print("🧪 Testing AI-Karen Auth System")
    print("=" * 40)
    
    token = test_dev_login()
    test_protected_endpoint(token)

