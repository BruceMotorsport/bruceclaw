#!/usr/bin/env python3
import socketserver, http.server, json, subprocess, os, time
from pathlib import Path

PORT = 9999
HOME = Path(os.path.expanduser("~"))

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            tools = ["files","shell","sms","contacts","calendar","battery","wifi","storage","web","memory","skills","mcp","notify","tts","install","camera","bluetooth"]
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"status":"ok","tools":tools}).encode())
        except: pass

    def do_POST(self):
        result = ""
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            msg = body.get("message","").lower()
            print(f"REQ: {msg[:60]}")

            # PRIORITY 1: Action commands (check FIRST)
            if "send sms" in msg or "send message" in msg or "text " in msg:
                number = ""
                text = "Hello"
                if "to" in msg:
                    after_to = msg.split("to")[-1].strip()
                    parts = after_to.split(None, 1)
                    number = parts[0].replace(" ","").replace("-","")
                    if len(parts) > 1:
                        text = parts[1].replace("say ","").replace("and say ","")
                if number:
                    subprocess.run(["termux-sms-send","-n",number,text], timeout=5)
                    result = f"SMS sent to {number}: {text}"
                else:
                    result = "Give me a phone number to send to"

            elif "open whatsapp" in msg or "whatsapp" in msg:
                subprocess.run(["am","start","-a","android.intent.action.MAIN","-c","android.intent.category.LAUNCHER","com.whatsapp"], timeout=5)
                result = "Opening WhatsApp"

            elif "open " in msg:
                app = msg.replace("open","").strip()
                subprocess.run(["am","start","-a","android.intent.action.MAIN","-c","android.intent.category.LAUNCHER"], timeout=5)
                result = f"Opening {app}"

            # PRIORITY 2: Specific data requests
            elif "battery" in msg:
                r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
                try:
                    d = json.loads(r.stdout)
                    if "voltage" in msg:
                        result = f"{d.get('voltage',0)/1000:.2f}V"
                    elif "percent" in msg or "level" in msg or "how much" in msg:
                        result = f"{d.get('percentage','?')}%"
                    else:
                        result = f"Battery: {d.get('percentage','?')}% at {d.get('voltage',0)/1000:.1f}V, {d.get('temperature','?')}C"
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
                    result = f"{len(contacts)} contacts" if contacts else "No contacts"
                except: result = r.stdout or "No contacts"

            elif "calendar" in msg or "event" in msg:
                r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=3)
                result = r.stdout or "No events"

            elif "read sms" in msg or "check sms" in msg or "show sms" in msg or "my sms" in msg:
                r = subprocess.run(["termux-sms-list","-l","5"], capture_output=True, text=True, timeout=3)
                try:
                    msgs = json.loads(r.stdout)
                    result = "\n".join([f"{m.get('address','?')}: {m.get('body','')[:50]}" for m in msgs[:5]])
                except: result = r.stdout or "No messages"

            elif "storage" in msg or "space" in msg:
                r = subprocess.run(["df","-h","/data"], capture_output=True, text=True, timeout=3)
                lines = r.stdout.strip().split("\n")
                result = lines[1] if len(lines) > 1 else "N/A"

            elif "screenshot" in msg:
                subprocess.run(["termux-screenshot",str(HOME/"screen.png")], timeout=5)
                result = "Screenshot saved"

            elif "camera" in msg or "photo" in msg:
                subprocess.run(["termux-camera-photo",str(HOME/"photo.jpg")], timeout=10)
                result = "Photo captured"

            elif "bluetooth" in msg or "scan" in msg:
                r = subprocess.run(["termux-bt-info"], capture_output=True, text=True, timeout=5)
                result = r.stdout or "No Bluetooth devices"

            elif "install" in msg:
                pkg = msg.replace("install","").strip()
                subprocess.run(["pkg","install","-y",pkg], capture_output=True, text=True, timeout=60)
                result = f"{pkg} installed"

            elif "notify" in msg:
                m = msg.replace("notify","").strip()
                subprocess.run(["termux-notification","-t","BruceClaw","-c",m], timeout=3)
                result = "Notification sent"

            elif "run " in msg or "command" in msg:
                cmd = msg.replace("run","").replace("command","").strip()
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = (r.stdout or r.stderr or "Done")[:500]

            elif "file" in msg:
                files = [f.name for f in HOME.iterdir() if not f.name.startswith(".")][:20]
                result = ", ".join(files)

            # PRIORITY 3: Only if nothing above matched
            elif "list" in msg and ("tool" in msg or "skill" in msg or "capabilit" in msg):
                result = "Tools: files, shell, sms, contacts, calendar, battery, wifi, storage, web, memory, skills, mcp, notify, tts, install, camera, bluetooth"

            else:
                result = "I can: battery, sms, contacts, calendar, files, camera, bluetooth, notifications. What do you need?"

            print(f"RES: {result[:60]}")
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply":result}).encode())
        except Exception as e:
            print(f"ERR: {e}")
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
