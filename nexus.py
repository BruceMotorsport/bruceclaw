#!/usr/bin/env python3
"""BruceClaw Nexus — Mobile AI Agent"""
import http.server, json, subprocess, os, glob, urllib.request, urllib.error

PORT = 8080
HOME = os.path.expanduser("~")

class NexusAgent:
    def __init__(self):
        self.api_key = os.environ.get("OPENCODE_ZEN_API_KEY", "")
        self.model = "mimo-v2.5"
        self.base_url = "https://opencode.ai/zen/go/v1"
        self.history = []
    
    def chat(self, message):
        self.history.append({"role": "user", "content": message})
        system = "You are BruceClaw — enthusiastic, cheerful, helpful. Use tools: list files [path], read file [path], run [command], sms, contacts, calendar, notify [msg], speak [text]. ASK before dangerous actions."
        messages = [{"role": "system", "content": system}] + self.history[-10:]
        
        data = json.dumps({"model": self.model, "messages": messages}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        reply = result["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": reply})
        return reply

class Handler(http.server.BaseHTTPRequestHandler):
    agent = NexusAgent()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "tools": ["files", "shell", "sms", "contacts", "calendar", "notify", "tts"]}).encode())
    
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length > 0 else {}
            message = body.get("message", body.get("messages", [{}])[-1].get("content", ""))
            print(f"Chat: {message[:50]}")
            reply = self.agent.chat(message)
            print(f"Reply: {reply[:50]}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply, "choices": [{"message": {"content": reply}}]}).encode())
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

if __name__ == "__main__":
    print(f"BruceClaw Nexus at http://localhost:{PORT}")
    print(f"API Key: {'SET' if os.environ.get('OPENCODE_ZEN_API_KEY') else 'NOT SET'}")
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
