#!/usr/bin/env python3
"""BruceClaw Nexus — Fast server with OpenClaw energy"""
import http.server, json, subprocess, os, glob

PORT = 8080
API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
BASE_URL = "https://opencode.ai/zen/go/v1"
history = []
HOME = os.path.expanduser("~")

def handle_tools(message):
    msg = message.lower()
    if "find" in msg or "folder" in msg or "search" in msg:
        name = ""
        skip = ["find","me","a","folder","in","my","files","that","call","can","you","the","is","it","for"]
        for word in message.split():
            if word.lower() not in skip:
                name = word
        if not name:
            return "What should I search for?"
        results = []
        for root, dirs, files in os.walk(HOME):
            for d in dirs:
                if name.lower() in d.lower():
                    results.append(os.path.join(root, d))
            for f in files:
                if name.lower() in f.lower():
                    results.append(os.path.join(root, f))
            if len(results) > 10: break
        return "Found:\n" + "\n".join(results[:10]) if results else f"No results for '{name}'"
    elif "list" in msg:
        files = [f for f in os.listdir(HOME) if not f.startswith(".")]
        return "\n".join(files[:30])
    return None

def chat(message):
    tool_result = handle_tools(message)
    if tool_result:
        return tool_result
    history.append({"role": "user", "content": message})
    system = """You are BruceClaw — an enthusiastic, capable AI assistant. 
You're direct, confident, and get things done. You use energy and enthusiasm 
but you're not over the top. Think of yourself as a sharp, capable partner 
who's always ready to tackle the next challenge. Keep replies focused and useful."""
    messages = [{"role": "system", "content": system}] + history[-10:]
    body = json.dumps({"model": "mimo-v2.5", "messages": messages})
    result = subprocess.run(["curl","-s","-X","POST",f"{BASE_URL}/chat/completions",
        "-H","Content-Type: application/json","-H",f"Authorization: Bearer {API_KEY}",
        "-d",body], capture_output=True, text=True, timeout=60)
    try:
        resp = json.loads(result.stdout)
        reply = resp["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        return reply
    except:
        return "Connection issue — try again"

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","agent":"BruceClaw"}')
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            msg = body.get("message", body.get("messages",[{}])[-1].get("content",""))
            reply = chat(msg)
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

print(f"BruceClaw running at http://localhost:{PORT}")
http.server.HTTPServer(("0.0.0.0",PORT),H).serve_forever()
