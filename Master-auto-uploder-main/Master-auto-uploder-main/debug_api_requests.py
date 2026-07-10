
import requests
import json
import base64

# Configuration
API_URL = "https://tandavclassesapi.classx.co.in"
# User input for token
TOKEN = input("Enter your Auth Token (Bearer token from login): ").strip()

def decode_token(token):
    try:
        parts = token.replace("Bearer ", "").split(".")
        if len(parts) > 1:
            padding = 4 - (len(parts[1]) % 4)
            decoded = base64.b64decode(parts[1] + "="*padding).decode()
            token_json = json.loads(decoded)
            return token_json.get("id") or token_json.get("user_id")
    except Exception as e:
        print(f"Token Decode Error: {e}")
    return "75308" # Fallback

def test_api():
    if not TOKEN.startswith("Bearer "):
         auth_header = f"Bearer {TOKEN}"
         raw_token = TOKEN
    else:
         auth_header = TOKEN
         raw_token = TOKEN.replace("Bearer ", "")

    user_id = decode_token(TOKEN)
    print(f"Using UserID: {user_id}")

    # Headers from ApnaEx (appex_v3.py)
    headers_apnaex = {
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "User-ID": str(user_id),
        "Authorization": raw_token, # Note: ApnaEx might use raw token without Bearer?
        "source": "website",
        "User_app_category": "",
        "Language": "en",
        # "Content-Type": "application/x-www-form-urlencoded", # Not using post
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "okhttp/4.9.1"
    }
    
    # Headers from Autoappx (appxdata.py)
    headers_autoappx = {
        'User-Agent': 'okhttp/4.9.1',
        'Accept-Encoding': 'gzip',
        'client-service': 'Appx',
        'auth-key': 'appxapi',
        'source': 'website',
        'user-id': str(user_id),
        'authorization': raw_token,
        'user_app_category': '',
        'language': 'en',
        'device_type': 'ANDROID'
    }

    endpoints = [
        f"/get/mycoursev2?userid={user_id}",
        f"/get/mycourse?userid={user_id}",
    ]

    print(f"\nScanning API: {API_URL}")

    # Test 1: ApnaEx Style Headers
    print("\n--- TEST 1: ApnaEx Style Headers ---")
    session = requests.Session()
    session.verify = False 
    
    for endpoint in endpoints:
        url = f"{API_URL}{endpoint}"
        try:
            print(f"Request: {url}")
            # Try with raw token first
            resp = session.get(url, headers=headers_apnaex)
            print(f"Status (Raw Token): {resp.status_code}")
            
            if resp.status_code == 200:
                print("SUCCESS!")
                print(str(resp.json())[:200])
            elif resp.status_code != 200:
                # Try with Bearer
                headers_apnaex["Authorization"] = auth_header
                resp = session.get(url, headers=headers_apnaex)
                print(f"Status (Bearer Token): {resp.status_code}")
                if resp.status_code == 200:
                    print("SUCCESS!")
                    print(str(resp.json())[:200])

        except Exception as e:
            print(f"Error: {e}")

    # Test 2: Autoappx Style Headers
    print("\n--- TEST 2: Autoappx Style Headers ---")
    for endpoint in endpoints:
        url = f"{API_URL}{endpoint}"
        try:
            print(f"Request: {url}")
            resp = session.get(url, headers=headers_autoappx)
            print(f"Status: {resp.status_code}")
             
            if resp.status_code == 200:
                print("SUCCESS!")
                print(str(resp.json())[:200])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    test_api()
