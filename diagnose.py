#!/usr/bin/env python3
"""Diagnostic for answering machine"""
import subprocess, json

print("=== BruceClaw Answering Machine Diagnostic ===\n")

# Check if bridge is running
print("1. Bridge status:")
try:
    r = subprocess.run(["curl", "-s", "http://localhost:9999/"], capture_output=True, text=True, timeout=3)
    if "BruceClaw" in r.stdout:
        print("   Bridge is running")
    else:
        print("   Bridge NOT running")
except:
    print("   Bridge NOT running")

# Check answering machine state
print("\n2. Answering machine state:")
try:
    r = subprocess.run(["curl", "-s", "-X", "POST", "http://localhost:9999/", 
                       "-H", "Content-Type: application/json",
                       "-d", '{"message":"answering machine status"}'], 
                       capture_output=True, text=True, timeout=5)
    print(f"   {r.stdout[:200]}")
except:
    print("   Could not check status")

# Check call state detection
print("\n3. Call state detection:")
try:
    r = subprocess.run(["dumpsys", "telephony.registry"], capture_output=True, text=True, timeout=3)
    state_line = [l for l in r.stdout.split("\n") if "mCallState" in l]
    if state_line:
        print(f"   {state_line[0].strip()}")
    else:
        print("   Could not find mCallState - permission issue?")
except Exception as e:
    print(f"   Error: {e}")

# Check permissions
print("\n4. Permissions:")
try:
    r = subprocess.run(["dumpsys", "package", "com.termux"], capture_output=True, text=True, timeout=3)
    perms = [l.strip() for l in r.stdout.split("\n") if "android.permission" in l.lower()]
    phone_perms = [p for p in perms if "PHONE" in p or "CALL" in p or "SMS" in p]
    if phone_perms:
        print(f"   Phone permissions found: {len(phone_perms)}")
        for p in phone_perms[:5]:
            print(f"     {p}")
    else:
        print("   No phone permissions found - this is the problem!")
except Exception as e:
    print(f"   Error: {e}")

print("\n=== If permissions are missing, run: ===")
print("termux-setup-storage")
print("Then grant SMS and Phone permissions in Android Settings > Apps > Termux > Permissions")
