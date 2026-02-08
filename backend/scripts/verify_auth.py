
import requests
import time

def test_auth():
    url = "http://localhost:8000/api/analyze"
    payload = {"text": "This is a test post for safety check."}
    
    print("\n--- Testing Authentication ---")
    
    # Test 1: No API Key
    try:
        resp = requests.post(url, json=payload)
        print(f"No API Key: Status {resp.status_code}")
        if resp.status_code == 401:
            print("PASS: Correctly rejected missing key")
        else:
            print(f"FAIL: Expected 401, got {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"FAIL: Request error: {e}")

    # Test 2: Invalid API Key
    try:
        resp = requests.post(url, json=payload, headers={"X-API-Key": "invalid-key"})
        print(f"Invalid API Key: Status {resp.status_code}")
        if resp.status_code == 401:
            print("PASS: Correctly rejected invalid key")
        else:
            print(f"FAIL: Expected 401, got {resp.status_code}")
    except Exception as e:
        print(f"FAIL: Request error: {e}")

    # Test 3: Valid API Key
    try:
        # demo-key-12345 is the default hardcoded valid key
        resp = requests.post(url, json=payload, headers={"X-API-Key": "demo-key-12345"})
        print(f"Valid API Key: Status {resp.status_code}")
        if resp.status_code == 200:
            print("PASS: Correctly accepted valid key")
        else:
            print(f"FAIL: Expected 200, got {resp.status_code}")
            with open("auth_debug.txt", "w") as f:
                f.write(resp.text)
            print("Response saved to auth_debug.txt")
    except Exception as e:
        print(f"FAIL: Request error: {e}")

if __name__ == "__main__":
    test_auth()
