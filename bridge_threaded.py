#!/usr/bin/env python3
import http.server, socketserver, json, subprocess, os
from pathlib import Path

PORT = 9999
HOME = Path(os.path.expanduser("~"))
TOOLS = {"files":"List files","shell":"Run commands","sms":"SMS","contacts":"Contacts","calendar":"Calendar","battery":"Battery","wifi":"WiFi","storage":"Storage","web":"Web","memory":"Memory","skills":"Skills","mcp":"MCP","notify":"Notify","tts":"TTS","install":"Install","camera":"Take photo","image":"Analyze image"}

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"status":"ok","tools":list(TOOLS.keys())}).encode())
        except: pass

    def do_POST(self):
        result = ""
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            msg = body.get("message","").lower()
            if "tool" in msg or "skill" in msg or "capabilit" in msg:
                result = json.dumps(TOOLS)
            elif "battery" in msg:
                r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No battery info"
            elif "wifi" in msg:
                r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No wifi"
            elif "contact" in msg:
                r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No contacts"
            elif "calendar" in msg or "event" in msg:
                r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No events"
            elif "sms" in msg:
                r = subprocess.run(["termux-sms-list", "-l", "10"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No messages"
            elif "file" in msg:
                files = [f.name for f in HOME.iterdir() if not f.name.startswith(".")][:30]
                result = json.dumps(files)
            elif "run" in msg or "command" in msg:
                cmd = msg.replace("run","").replace("command","").strip()
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = r.stdout or r.stderr or "Done"
            elif "storage" in msg:
                r = subprocess.run(["df", "-h", "/data"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No storage info"
            elif "install" in msg:
                pkg = msg.replace("install","").strip()
                r = subprocess.run(["pkg", "install", "-y", pkg], capture_output=True, text=True, timeout=60)
                result = r.stdout or "Installed"
            elif "notify" in msg:
                m = msg.replace("notify","").strip()
                subprocess.run(["termux-notification", "-t", "BruceClaw", "-c", m], timeout=5)
                result = "Notification sent"
            elif "camera" in msg or "photo" in msg or "picture" in msg:
                subprocess.run(["termux-camera-photo", str(HOME / "photo.jpg")], timeout=10)
                result = "Photo saved to ~/photo.jpg"
            else:
                result = "Tools: " + ", ".join(TOOLS.keys())
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply":result}).encode())
        except Exception as e:
            try:
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(json.dumps({"reply":"Error: "+str(e)}).encode())
            except: pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def log_message(self,*a): pass

print("BruceClaw Bridge at http://localhost:"+str(PORT))
ThreadedHTTPServer(("0.0.0.0",PORT),H).serve_forever()
