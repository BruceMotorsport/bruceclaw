#!/usr/bin/env python3
"""
BruceClaw Bridge — Connects Android app to OpenClaw Gateway
Runs inside OpenClaw's environment, uses all its tools
"""
import http.server
import json
import subprocess
import os
import sys

PORT = 8080

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "agent": "BruceClaw",
            "bridge": "OpenClaw Gateway"
        }).encode())
    
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            message = body.get("message", "")
            
            # Route through OpenClaw's chat
            reply = self.openclaw_chat(message)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "reply": reply,
                "choices": [{"message": {"content": reply}}]
            }).encode())
            
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": f"Error: {e}"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def openclaw_chat(self, message):
        """Send message through OpenClaw's gateway"""
        try:
            # Use OpenClaw's CLI to send message
            result = subprocess.run(
                ["openclaw", "chat", "--once", message],
                capture_output=True, text=True, timeout=60
            )
            return result.stdout.strip() or result.stderr.strip() or "No response"
        except FileNotFoundError:
            # OpenClaw not installed, use direct API
            return self.direct_api(message)
        except subprocess.TimeoutExpired:
            return "Timeout — try again"
        except Exception as e:
            return f"Error: {e}"
    
    def direct_api(self, message):
        """Direct API call as fallback"""
        import urllib.request
        api_key = os.environ.get("OPENCODE_ZEN_API_KEY", "")
        url = "https://opencode.ai/zen/go/v1/chat/completions"
        data = json.dumps({
            "model": "mimo-v2.5",
            "messages": [{"role": "user", "content": message}]
        }).encode()
        
        req = urllib.request.Request(url, data=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"BruceClaw Bridge at http://localhost:{PORT}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), BridgeHandler)
    server.serve_forever()
