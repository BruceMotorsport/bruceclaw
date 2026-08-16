#!/usr/bin/env python3
import socketserver, http.server, json, subprocess, os, time, sys
from pathlib import Path

PORT = 9999
HOME = Path(os.path.expanduser("~"))
TOOLS = {"files":"List files","shell":"Run commands","sms":"SMS","contacts":"Contacts","calendar":"Calendar","battery":"Battery","wifi":"WiFi","storage":"Storage","web":"Web","memory":"Memory","skills":"Skills","mcp":"MCP","notify":"Notify","tts":"TTS","install":"Install","camera":"Take photo","screenshot":"Capture screen","bluetooth":"Bluetooth scan"}
TOOLS_JSON = json.dumps(TOOLS).encode()

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[{time.strftime('%H:%M:%S')}] GET from {self.client_address[0]}", flush=True)
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(TOOLS_JSON)

    def do_POST(self):
        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length",0)))
            body = json.loads(raw)
            msg = body.get("message","").lower()
            t0 = time.time()
            print(f"[{time.strftime('%H:%M:%S')}] POST from {self.client_address[0]}: {msg[:80]}", flush=True)

            result = ""
            if "tool" in msg or "capabilit" in msg or "what can" in msg:
                result = TOOLS_JSON.decode()
            elif "battery" in msg:
                r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "N/A"
            elif "wifi" in msg:
                r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "N/A"
            elif "contact" in msg:
                r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "No contacts"
            elif "calendar" in msg or "event" in msg:
                r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "No events"
            elif "sms" in msg:
                r = subprocess.run(["termux-sms-list", "-l", "10"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "No messages"
            elif "file" in msg:
                result = json.dumps([f.name for f in HOME.iterdir() if not f.name.startswith(".")][:30])
            elif "run" in msg or "command" in msg:
                cmd = msg.replace("run","").replace("command","").strip()
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = r.stdout or r.stderr or "Done"
            elif "camera" in msg or "photo" in msg:
                subprocess.run(["termux-camera-photo", str(HOME / "photo.jpg")], timeout=10)
                result = "Photo saved"
            elif "bluetooth" in msg or "scan" in msg:
                r = subprocess.run(["termux-bluetooth-scan"], capture_output=True, text=True, timeout=10)
                result = r.stdout or "No devices"
            elif "screenshot" in msg:
                result = "Screenshot feature coming soon"
            else:
                result = "Tools: " + ", ".join(TOOLS.keys())

            elapsed = round((time.time()-t0)*1000)
            resp = json.dumps({"reply": result, "ms": elapsed}).encode()
            print(f"[{time.strftime('%H:%M:%S')}] Reply ({elapsed}ms): {result[:80]}", flush=True)
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(resp)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ERROR: {e}", flush=True)
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

print(f"BruceClaw Bridge at http://localhost:{PORT}", flush=True)
print("Waiting for connections...", flush=True)
sys.stdout.flush()
FastServer(("0.0.0.0",PORT),H).serve_forever()
