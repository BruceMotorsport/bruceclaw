#!/usr/bin/env python3
import socketserver, http.server, json, subprocess, os, time, sys
from pathlib import Path

PORT = 9999
HOME = Path(os.path.expanduser("~"))
TOOLS = {"files":"List files","shell":"Run commands","sms":"SMS","contacts":"Contacts","calendar":"Calendar","battery":"Battery","wifi":"WiFi","storage":"Storage","web":"Web","memory":"Memory","skills":"Skills","mcp":"MCP","notify":"Notify","tts":"TTS","install":"Install","camera":"Camera","screenshot":"Screenshot","bluetooth":"Bluetooth"}

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

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

            if "tool" in msg or "capabilit" in msg or "what can" in msg:
                result = "I can: " + ", ".join(TOOLS.keys())
            elif "battery" in msg:
                r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
                try:
                    d = json.loads(r.stdout)
                    result = f"Battery: {d.get('percentage','?')}% at {d.get('voltage',0)/1000:.1f}V"
                except: result = r.stdout or "N/A"
            elif "wifi" in msg:
                r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=3)
                try:
                    d = json.loads(r.stdout)
                    result = f"WiFi: {d.get('ssid','?')} ({d.get('link_speed','?')}Mbps)"
                except: result = r.stdout or "N/A"
            elif "contact" in msg:
                r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=3)
                try:
                    contacts = json.loads(r.stdout)
                    result = f"{len(contacts)} contacts found" if contacts else "No contacts"
                except: result = r.stdout or "No contacts"
            elif "calendar" in msg or "event" in msg:
                r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "No upcoming events"
            elif "sms" in msg and "send" not in msg:
                r = subprocess.run(["termux-sms-list", "-l", "5"], capture_output=True, text=True, timeout=3)
                try:
                    msgs = json.loads(r.stdout)
                    result = f"{len(msgs)} recent messages" if msgs else "No messages"
                except: result = r.stdout or "No messages"
            elif "send sms" in msg or "send message" in msg:
                parts = msg.split("to")[-1].strip().split()
                number = parts[0] if parts else ""
                text = msg.split("message")[-1].strip() if "message" in msg else msg.split("to")[-1].strip()
                subprocess.run(["termux-sms-send", "-n", number, text], timeout=5)
                result = f"SMS sent to {number}"
            elif "file" in msg:
                files = [f.name for f in HOME.iterdir() if not f.name.startswith(".")][:20]
                result = f"Files: {', '.join(files)}"
            elif "run" in msg or "command" in msg:
                cmd = msg.replace("run","").replace("command","").strip()
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = (r.stdout or r.stderr or "Done")[:500]
            elif "camera" in msg or "photo" in msg:
                subprocess.run(["termux-camera-photo", str(HOME / "photo.jpg")], timeout=10)
                result = "Photo captured"
            elif "bluetooth" in msg or "scan" in msg:
                try:
                    r = subprocess.run(["termux-bt-info"], capture_output=True, text=True, timeout=5)
                    result = r.stdout or "No Bluetooth devices found"
                except:
                    result = "Bluetooth scan not available on this device"
            elif "install" in msg:
                pkg = msg.replace("install","").strip()
                subprocess.run(["pkg", "install", "-y", pkg], capture_output=True, text=True, timeout=60)
                result = f"{pkg} installed"
            elif "storage" in msg:
                r = subprocess.run(["df", "-h", "/data"], capture_output=True, text=True, timeout=3)
                result = r.stdout.split("\n")[1] if len(r.stdout.split("\n")) > 1 else "N/A"
            elif "notify" in msg:
                m = msg.replace("notify","").strip()
                subprocess.run(["termux-notification", "-t", "BruceClaw", "-c", m], timeout=3)
                result = "Notification sent"
            else:
                result = "I can help with: " + ", ".join(TOOLS.keys())

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

print(f"BruceClaw Bridge at http://localhost:{PORT}")
FastServer(("0.0.0.0",PORT),H).serve_forever()
