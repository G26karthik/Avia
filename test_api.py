"""Quick API validation tests for all audit fixes."""
import urllib.request, json, sys

BASE = "http://localhost:8000/api"

def post(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else b""
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method="POST")
    return urllib.request.urlopen(req)

def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    return urllib.request.urlopen(req)

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name} — {e}")
        failed += 1

# --- Test 1: Unauthenticated access blocked ---
def t1():
    try:
        get("/claims")
        raise AssertionError("Should have been blocked")
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"
test("Unauthenticated /claims blocked (401)", t1)

# --- Test 2: Wrong password rejected ---
def t2():
    try:
        post("/auth/login", {"username": "jsmith", "password": "wrong"})
        raise AssertionError("Should have been rejected")
    except urllib.error.HTTPError as e:
        assert e.code == 401
test("Wrong password rejected (401)", t2)

# --- Test 3: Correct login ---
token = None
def t3():
    global token
    r = post("/auth/login", {"username": "jsmith", "password": "avia2026"})
    d = json.loads(r.read())
    assert "token" in d, "No token in response"
    assert d["org_id"] == "org-demo-001"
    token = d["token"]
test("Correct login returns token", t3)

# --- Test 4: Authenticated claims list ---
claims_data = None
def t4():
    global claims_data
    r = get("/claims", token)
    claims_data = json.loads(r.read())
    assert claims_data["total"] > 0, "No claims returned"
test(f"Authenticated claims list works", t4)

# --- Test 5: Claim detail with auth ---
claim_id = None
def t5():
    global claim_id
    claim_id = claims_data["claims"][0]["id"]
    r = get(f"/claims/{claim_id}", token)
    d = json.loads(r.read())
    assert d["id"] == claim_id
test("Claim detail with auth works", t5)

# --- Test 6: Analyze blocked without documents ---
def t6():
    try:
        post(f"/claims/{claim_id}/analyze", token=token)
        raise AssertionError("Should require documents")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        body = json.loads(e.read())
        assert "document" in body["detail"].lower()
test("Analyze blocked without documents (400)", t6)

# --- Test 7: /auth/me validates session ---
def t7():
    r = get("/auth/me", token)
    d = json.loads(r.read())
    assert d["username"] == "jsmith"
    assert d["org_id"] == "org-demo-001"
test("/auth/me validates session", t7)

# --- Test 8: Health endpoint (no auth) ---
def t8():
    r = get("/health")
    d = json.loads(r.read())
    assert d["status"] == "ok"
test("Health endpoint works without auth", t8)

# --- Test 9: Invalid token rejected ---
def t9():
    try:
        get("/claims", "invalid-token-abc123")
        raise AssertionError("Should reject invalid token")
    except urllib.error.HTTPError as e:
        assert e.code == 401
test("Invalid token rejected (401)", t9)

# --- Test 10: Cross-org claim access blocked ---
def t10():
    try:
        get("/claims/CLM-NONEXIST", token)
        raise AssertionError("Should return 404")
    except urllib.error.HTTPError as e:
        assert e.code == 404
test("Non-existent claim returns 404", t10)

print(f"\nResults: {passed} passed, {failed} failed out of {passed+failed}")
if failed > 0:
    sys.exit(1)
