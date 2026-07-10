
import asyncio
import httpx
import json

# Configuration
API_URL = "https://tandavclassesapi.classx.co.in"
# USER_ID will be fetched dynamically if possible
TOKEN = input("Enter your Auth Token (Bearer token from login): ").strip()

async def test_api():
    if not TOKEN.startswith("Bearer "):
         auth_header = f"Bearer {TOKEN}"
    else:
         auth_header = TOKEN

    base_headers = {
        'User-Agent': 'okhttp/4.9.1',
        'Accept-Encoding': 'gzip',
        'client-service': 'Appx',
        'auth-key': 'appxapi',
        'source': 'website', # Will try switching this
        'language': 'en',
        'device_type': 'ANDROID',
        'authorization': auth_header
    }

    print(f"Testing API: {API_URL}")
    
    async with httpx.AsyncClient(verify=False) as client:
        # 1. Try to get profile to verify token and get correct UserID
        print("\n--- STEP 1: Verify Token & Get Profile ---")
        user_id = None
        try:
             # Try getting profile
             resp = await client.get(f"{API_URL}/get/myprofile", headers=base_headers)
             print(f"Profile Status: {resp.status_code}")
             if resp.status_code == 200:
                 data = resp.json()
                 print("Profile Data Found")
                 user_data = data.get('data', {})
                 user_id = user_data.get('id') or user_data.get('user_id') or user_data.get('_id')
                 print(f"Detected UserID from Profile: {user_id}")
             else:
                 print(f"Profile Failed: {resp.text[:100]}")
        except Exception as e:
             print(f"Profile Error: {e}")

        # If we couldn't get user_id from profile, try extracting from token manually (simple decode)
        if not user_id:
            try:
                # Very basic decode without verify
                parts = TOKEN.replace("Bearer ", "").split(".")
                if len(parts) > 1:
                    import base64
                    padding = 4 - (len(parts[1]) % 4)
                    decoded = base64.b64decode(parts[1] + "="*padding).decode()
                    token_json = json.loads(decoded)
                    user_id = token_json.get("id") or token_json.get("user_id")
                    print(f"Extracted UserID from Token: {user_id}")
            except Exception as e:
                print(f"Token Decode Error: {e}")
                user_id = "75308" # Fallback from previous logs

        # 2. Test Course Endpoints with variations
        print(f"\n--- STEP 2: Test Course Endpoints (UserID: {user_id}) ---")
        
        scenarios = [
            ("Standard", base_headers),
            ("Source: Android", {**base_headers, "source": "android"}),
            ("No UserID Header", {k:v for k,v in base_headers.items()}), 
            ("Explicit UserID Header", {**base_headers, "user-id": str(user_id)}),
        ]

        endpoints = [
             f"/get/mycoursev2?userid={user_id}",
             f"/get/mycourse?userid={user_id}",
             f"/get/mycoursev2", # Rely on token/header
        ]

        for name, headers in scenarios:
            print(f"\n> Scenario: {name}")
            for endpoint in endpoints:
                url = f"{API_URL}{endpoint}"
                try:
                    resp = await client.get(url, headers=headers)
                    print(f"   GET {endpoint} -> {resp.status_code}")
                    if resp.status_code == 200:
                         data = resp.json()
                         if isinstance(data, dict) and data.get("data"):
                             print("   SUCCESS! Data found.")
                             # print(str(data)[:100])
                         else:
                             print("   200 OK but empty/invalid data.")
                except Exception as e:
                    print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
