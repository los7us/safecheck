
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/analyze"
API_KEY = "demo-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_security():
    print("\n--- Testing Security Controls ---")
    results = []

    # 1. Input Validation - Bad URL Scheme
    print("\n[Test 1] Bad URL Scheme (javascript:)")
    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json={"url": "javascript:alert(1)"})
        if resp.status_code == 422:
            print("PASS: Rejected bad scheme")
            results.append(True)
        else:
            print(f"FAIL: Expected 422, got {resp.status_code}")
            print(resp.text)
            results.append(False)
    except Exception as e:
        print(f"Error: {e}")
        results.append(False)

    # 2. Input Validation - Localhost (SSRF)
    print("\n[Test 2] Localhost URL (SSRF)")
    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json={"url": "http://localhost:8080/admin"})
        if resp.status_code == 422:
            print("PASS: Rejected localhost")
            results.append(True)
        else:
            print(f"FAIL: Expected 422, got {resp.status_code}")
            print(resp.text)
            results.append(False)
    except Exception as e:
        print(f"Error: {e}")
        results.append(False)

    # 3. Input Validation - Private IP (SSRF)
    print("\n[Test 3] Private IP (SSRF)")
    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json={"url": "http://192.168.1.1/router"})
        if resp.status_code == 422:
            print("PASS: Rejected private IP")
            results.append(True)
        else:
            print(f"FAIL: Expected 422, got {resp.status_code}")
            print(resp.text)
            results.append(False)
    except Exception as e:
        print(f"Error: {e}")
        results.append(False)
        
    # 4. Request Size Limit
    print("\n[Test 4] Oversized Payload (>1MB)")
    try:
        large_text = "A" * (1024 * 1024 + 100) # 1MB + 100 bytes
        resp = requests.post(BASE_URL, headers=HEADERS, json={"text": large_text})
        if resp.status_code == 413:
            print("PASS: Rejected large payload")
            results.append(True)
        else:
            print(f"FAIL: Expected 413, got {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"Error: {e}")
        results.append(False)

    # 5. CORS Check (Preflight)
    print("\n[Test 5] CORS from Unauthorized Origin")
    try:
        cors_headers = {
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-API-Key"
        }
        resp = requests.options(BASE_URL, headers=cors_headers)
        
        allow_origin = resp.headers.get("access-control-allow-origin")
        if allow_origin is None or allow_origin != "http://evil.com":
            print(f"PASS: Origin not allowed (Header: {allow_origin})")
            results.append(True)
        else:
            print(f"FAIL: Allowed evil origin: {allow_origin}")
            results.append(False)
    except Exception as e:
        print(f"Error: {e}")
        results.append(False)

    print(f"\nFinal Summary: {sum(results)}/{len(results)} Tests Passed")

if __name__ == "__main__":
    test_security()
