#!/usr/bin/env python3
"""BruceClaw Nexus — handles both app formats"""
import http.server, json, subprocess, os

PORT = 8080
API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
BASE_URL = "https://opencode.ai/zen/go/v1"
history = []

def chat(message):
    history.append({"role": "user", "content": message})
    system = "You are BruceClaw — enthusiastic and cheerful! Keep replies short."
    messages = [{"role": "system", "content": system}] + history[-10:]
    
    body = json.dumps({"model": "mimo-v2.5", "messages": messages})
    
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{BASE_URL}/chat/completions",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-d", body
    ], capture_output=True, text=True, timeout=60)
    
    try:
        resp = json.loads(result.stdout)
        reply = resp["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        return reply
    except:
        return f"Error: {result.stdout[:200]}"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())
    
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
            
            # Handle both formats
            if "message" in body:
                msg = body["message"]
            elif "messages" in body:
                msg = body["messages"][-1].get("content", "")
            else:
                msg = ""
            
            print(f">>> {msg[:50]}")
            reply = chat(msg)
            print(f"<<< {reply[:80]}")
            
            # Send response in both formats
            response = {
                "reply": reply,
                "choices": [{"message": {"content": reply}}],
                "message": reply
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "reply": f"Error: {e}"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, *a): pass

print(f"BruceClaw Nexus at http://localhost:{PORT}")
print(f"API Key: {'SET' if API_KEY else 'NOT SET'}")
http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
