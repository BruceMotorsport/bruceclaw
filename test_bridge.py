#!/usr/bin/env python3
"""Test bridge tools directly"""
import urllib.request, json

BRIDGE = "http://localhost:9999"

def test(name, msg):
    try:
        data = json.dumps({"message": msg}).encode()
        req = urllib.request.Request(BRIDGE, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            reply = result.get("reply", "No reply")
            print(f"[OK] {name}: {reply[:80]}")
            return True
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False

print("=== BruceClaw Bridge Test ===\n")

tests = [
    ("Battery", "what's my battery"),
    ("Storage", "how much storage"),
    ("Answering ON", "answering machine on"),
    ("Answering Status", "answering machine status"),
    ("Call Log", "call log"),
    ("Contacts", "contacts"),
    ("Location", "where am i"),
]

passed = 0
for name, msg in tests:
    if test(name, msg):
        passed += 1

print(f"\n=== {passed}/{len(tests)} tests passed ===")
