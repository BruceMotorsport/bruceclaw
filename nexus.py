#!/usr/bin/env python3
"""BruceClaw Nexus — Fast Python HTTP, no curl"""
import http.server, json, os, urllib.request, urllib.error

PORT = 8080
API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
BASE_URL = "https://opencode.ai/zen/go/v1"

def chat(message, api_key=None, model_name=None):
    key = api_key or API_KEY
    mdl = model_name or "mimo-v2.5"
    messages = [
        {"role":"system","content":"You are BruceClaw — direct, capable, enthusiastic. Keep replies under 80 words."},
        {"role":"user","content":message}
    ]
    body = json.dumps({"model":mdl,"messages":messages}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={
            "Content-Type":"application/json",
            "Authorization":f"Bearer {key}"
        }
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            msg = body.get("message","")
            api_key = body.get("apiKey","")
            model_name = body.get("model","mimo-v2.5")
            reply = chat(msg, api_key, model_name)
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply":reply,"choices":[{"message":{"content":reply}}]}).encode())
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply":f"Error: {e}"}).encode())
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()
    def log_message(self,*a): pass

print(f"BruceClaw at http://localhost:{PORT}")
http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
