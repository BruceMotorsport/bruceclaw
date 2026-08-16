#!/usr/bin/env python3
import http.server, json, subprocess, os, time
from pathlib import Path

PORT = 8080
HOME = Path(os.path.expanduser("~"))
TOOLS = {
    "files": "List, read, write files",
    "shell": "Run shell commands",
    "sms": "Read/send SMS",
    "contacts": "Read contacts",
    "calendar": "Read calendar",
    "battery": "Check battery",
    "wifi": "Check WiFi",
    "storage": "Check storage",
    "web": "Browse internet",
    "memory": "Read/write memory",
    "skills": "List skills",
    "mcp": "MCP servers",
    "notify": "Send notifications",
    "tts": "Text to speech",
    "install": "Install packages"
}

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            resp = json.dumps({"status": "ok", "tools": list(TOOLS.keys())}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp)
        except:
            pass

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            msg = body.get("message", "").lower()
            result = ""

            if "tool" in msg or "skill" in msg or "capabilit" in msg:
                result = json.dumps(TOOLS)
            elif "battery" in msg:
                r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "Battery unavailable"
            elif "wifi" in msg:
                r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "WiFi unavailable"
            elif "storage" in msg:
                r = subprocess.run(["df", "-h", "/data"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "Storage unavailable"
            elif "contact" in msg:
                r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "No contacts"
            elif "calendar" in msg or "event" in msg:
                r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "No events"
            elif "sms" in msg or "message" in msg:
                r = subprocess.run(["termux-sms-list", "-l", "10"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "No messages"
            elif "file" in msg:
                p = HOME
                files = [f.name for f in p.iterdir() if not f.name.startswith(".")][:30]
                result = json.dumps(files)
            elif "run" in msg or "command" in msg:
                cmd = msg.replace("run", "").replace("command", "").strip()
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = r.stdout or r.stderr or "Done"
            elif "install" in msg:
                pkg = msg.replace("install", "").strip()
                r = subprocess.run(["pkg", "install", "-y", pkg], capture_output=True, text=True, timeout=60)
                result = r.stdout or "Installed"
            elif "notify" in msg:
                m = msg.replace("notify", "").strip()
                subprocess.run(["termux-notification", "-t", "BruceClaw", "-c", m])
                result = "Notification sent"
            else:
                result = "Tools: " + ", ".join(TOOLS.keys())

            resp = json.dumps({"reply": result, "choices": [{"message": {"content": result}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp)
        except Exception as e:
            try:
                resp = json.dumps({"reply": "Error: " + str(e)}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except:
                pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *a):
        pass

print("BruceClaw Bridge v2 at http://localhost:8080")
http.server.HTTPServer(("0.0.0.0", PORT), H).serve_forever()
