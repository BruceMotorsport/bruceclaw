#!/usr/bin/env python3
"""BruceClaw Nexus — with tool handling"""
import http.server, json, subprocess, os, glob

PORT = 8080
API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
BASE_URL = "https://opencode.ai/zen/go/v1"
history = []
HOME = os.path.expanduser("~")

def handle_tools(message):
    """Check if message needs a tool, return result or None"""
    msg = message.lower()
    
    if "find" in msg or "folder" in msg or "search" in msg:
        # Find folders
        name = message.split("folder")[-1].strip().split()[-1] if "folder" in message else ""
        results = []
        for root, dirs, files in os.walk(HOME):
            for d in dirs:
                if name.lower() in d.lower():
                    results.append(os.path.join(root, d))
            if len(results) > 5:
                break
        if results:
            return f"Found folders:\n" + "\n".join(results[:5])
        return f"No folders found matching '{name}'"
    
    elif "list files" in msg or "show files" in msg:
        path = HOME
        if "in" in message:
            parts = message.split("in")[-1].strip().split()
            if parts:
                path = parts[0]
        files = []
        for f in sorted(glob.glob(os.path.join(path, "*"))):
            name = os.path.basename(f)
            if not name.startswith("."):
                files.append(f"{'📁' if os.path.isdir(f) else '📄'} {name}")
        return "\n".join(files[:20]) if files else "No files found"
    
    elif "read file" in msg:
        path = message.replace("read file", "").strip()
        try:
            with open(path, "r") as f:
                return f.read()[:2000]
        except:
            return f"Can't read: {path}"
    
    return None

def chat(message):
    # Check tools first
    tool_result = handle_tools(message)
    if tool_result:
        return tool_result
    
    history.append({"role": "user", "content": message})
    system = "You are BruceClaw — enthusiastic and cheerful! Keep replies short."
    messages = [{"role": "system", "content": system}] + history[-10:]
    
    body = json.dumps({"model": "mimo-v2.5", "messages": messages})
    result = subprocess.run([
        "curl", "-s", "-X", "POST", f"{BASE_URL}/chat/completions",
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
            msg = body.get("message", body.get("messages", [{}])[-1].get("content", ""))
            print(f">>> {msg[:50]}")
            reply = chat(msg)
            print(f"<<< {reply[:80]}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply, "choices": [{"message": {"content": reply}}]}).encode())
        except Exception as e:
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
http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
