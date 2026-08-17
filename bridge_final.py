#!/usr/bin/env python3
"""BruceClaw Bridge v8 - Walkie-Talkie between User and Mimo"""
import socketserver, http.server, json, subprocess, os, time, threading, re, urllib.request
from pathlib import Path
from datetime import datetime

PORT = 9999
HOME = Path(os.path.expanduser("~"))
MESSAGES_DIR = HOME / "bruceclaw_messages"
MESSAGES_DIR.mkdir(exist_ok=True)
SCRIPT_DIR = Path(__file__).parent

# API config
API_BASE = "https://opencode.ai/zen/go/v1"
MODEL = "mimo-v2.5"
API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
if not API_KEY:
    for p in [HOME / ".bruceclaw_config.json", HOME / ".openclaw" / "openclaw.json"]:
        if p.exists():
            try:
                with open(p) as f:
                    c = json.load(f)
                API_KEY = c.get("api_key", c.get("providers",{}).get("openai",{}).get("apiKey",""))
                if API_KEY: break
            except: pass

# Load knowledge base
KB = {}
KB_PATH = SCRIPT_DIR / "knowledge_base.json"
try:
    with open(KB_PATH) as f: KB = json.load(f)
except: pass

# Answering machine state
answering_machine = {"enabled": False, "messages": [], "conversation_log": []}

# System prompt for Mimo
MIMO_PROMPT = """You are BruceClaw, Bruce Nigel's AI assistant. You are a walkie-talkie - the Python bot handles everything on the phone, you just decide what to do.

WHEN THE USER ASKS YOU TO DO SOMETHING ON THE PHONE:
- Reply with a TOOL CALL in this exact format: TOOL:tool_name:arguments
- Examples:
  - TOOL:answering_machine:on
  - TOOL:send_sms:0772256655,hi there
  - TOOL:make_call:0772256655
  - TOOL:battery
  - TOOL:camera
  - TOOL:location
  - TOOL:contacts
  - TOOL:call_log
  - TOOL:storage
  - TOOL:tts:hello world
  - TOOL:notify:notification text
  - TOOL:shell:ls -la
  - TOOL:open_app:whatsapp
  - TOOL:learn:some fact to remember

AVAILABLE TOOLS:
answering_machine(on/off) - auto-answer calls
send_sms(number,message) - send SMS
make_call(number) - dial number
battery - check battery
camera - take photo
location - get GPS
contacts - list contacts
call_log - recent calls
storage - check storage
tts(text) - speak text
notify(message) - send notification
shell(command) - run command
open_app(name) - open app
learn(fact) - remember something
eavesdrop(start/stop) - record audio
volume(up/down/mute) - control volume
screenshot - take screenshot
wifi(status/scan/on/off) - wifi control
bluetooth(scan/on/off) - bluetooth control

WHEN THE USER JUST WANTS TO CHAT:
- Just respond normally, no tool call needed
- Be friendly, concise, no emojis
- Answer questions about Bruce's businesses if asked

BUSINESSES:
- Bruce Racing Pvt Ltd: 4x4 diesel workshop, 767 Millagahawatte Road, Malabe
- Labour rate: Rs 6,500/hr
- Services: Engine overhaul, transmission repair, diesel diagnostics
- GoGetter Digital: 24/7 AI agency
- GoGetter Academy: Education platform

RULES:
- Never use emojis
- Never list all capabilities unless asked
- Be direct and concise
- If asked to do something on the phone, reply with TOOL:tool_name:arguments
"""

def call_mimo(messages):
    """Call Mimo (LLM)"""
    if not API_KEY:
        return "I can't connect to Mimo right now. Please try again."
    try:
        payload = json.dumps({
            "model": MODEL,
            "messages": [{"role": "system", "content": MIMO_PROMPT}] + messages,
            "max_tokens": 300,
            "temperature": 0.7
        }).encode()
        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Mimo error: {e}"

def execute_tool(tool_str):
    """Execute a tool command from Mimo"""
    print(f"TOOL: {tool_str}")
    try:
        parts = tool_str.split(":", 2)
        tool = parts[0].strip()
        args = parts[1].strip() if len(parts) > 1 else ""
        extra = parts[2].strip() if len(parts) > 2 else ""

        if tool == "answering_machine":
            answering_machine["enabled"] = args == "on"
            return f"Answering machine {'enabled' if args == 'on' else 'disabled'}"

        elif tool == "send_sms":
            number, text = args.split(",", 1) if "," in args else (args, "Hello")
            subprocess.run(["termux-sms-send", "-n", number.strip(), text.strip()], timeout=10)
            return f"SMS sent to {number.strip()}: {text.strip()}"

        elif tool == "make_call":
            subprocess.run(["am", "start", "-a", "android.intent.action.DIAL", "-d", f"tel:{args}"], timeout=5)
            return f"Calling {args}..."

        elif tool == "battery":
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
            d = json.loads(r.stdout)
            return f"Battery: {d.get('percentage','?')}% at {d.get('voltage',0)/1000:.1f}V"

        elif tool == "camera":
            path = str(HOME / f"photo_{int(time.time())}.jpg")
            subprocess.run(["termux-camera-photo", path], timeout=15)
            return f"Photo saved: {path}" if os.path.exists(path) else "Camera failed"

        elif tool == "location":
            r = subprocess.run(["termux-location", "-p", "gps"], capture_output=True, text=True, timeout=10)
            d = json.loads(r.stdout)
            return f"Location: {d.get('latitude','?')}, {d.get('longitude','?')}"

        elif tool == "contacts":
            r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=5)
            contacts = json.loads(r.stdout)
            return f"{len(contacts)} contacts found"

        elif tool == "call_log":
            r = subprocess.run(["termux-call-log", "-l", "5"], capture_output=True, text=True, timeout=5)
            calls = json.loads(r.stdout)
            lines = [f"{c.get('number','?')} ({c.get('type','?')})" for c in calls[:5]]
            return "Recent calls: " + ", ".join(lines)

        elif tool == "storage":
            r = subprocess.run(["df", "-h", "/data"], capture_output=True, text=True, timeout=3)
            lines = r.stdout.strip().split("\n")
            return f"Storage: {lines[1]}" if len(lines) > 1 else "N/A"

        elif tool == "tts":
            subprocess.run(["termux-tts-speak", args], timeout=10)
            return f"Speaking: {args}"

        elif tool == "notify":
            subprocess.run(["termux-notification", "-t", "BruceClaw", "-c", args], timeout=3)
            return "Notification sent"

        elif tool == "shell":
            r = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=30)
            return (r.stdout or r.stderr or "Done")[:200]

        elif tool == "open_app":
            apps = {"whatsapp": "com.whatsapp", "chrome": "com.android.chrome",
                    "settings": "com.android.settings", "camera": "com.android.camera"}
            pkg = apps.get(args.lower(), args)
            subprocess.run(["monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, timeout=5)
            return f"Opening {args}..."

        elif tool == "learn":
            if "learned_facts" not in KB:
                KB["learned_facts"] = []
            KB["learned_facts"].append({"fact": args, "added": datetime.now().strftime("%Y-%m-%d %H:%M")})
            with open(KB_PATH, "w") as f:
                json.dump(KB, f, indent=2)
            return f"Learned: {args}"

        elif tool == "eavesdrop":
            return "Eavesdrop " + ("started" if args == "on" else "stopped")

        elif tool == "volume":
            if args == "mute":
                subprocess.run(["termux-volume", "music", "0"], timeout=3)
            elif args == "up":
                subprocess.run(["termux-volume", "music", "15"], timeout=3)
            else:
                subprocess.run(["termux-volume", "music", "7"], timeout=3)
            return f"Volume {args}"

        elif tool == "screenshot":
            path = str(HOME / f"screen_{int(time.time())}.png")
            subprocess.run(["termux-screenshot", path], timeout=5)
            return f"Screenshot: {path}" if os.path.exists(path) else "Failed"

        elif tool == "wifi":
            if args == "status":
                r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=3)
                d = json.loads(r.stdout)
                return f"WiFi: {d.get('ssid','?')}"
            elif args == "on":
                subprocess.run(["termux-wifi-enable", "on"], timeout=3)
                return "WiFi on"
            elif args == "off":
                subprocess.run(["termux-wifi-enable", "off"], timeout=3)
                return "WiFi off"
            return "WiFi status"

        elif tool == "bluetooth":
            if args == "scan":
                r = subprocess.run(["termux-bt-scan"], capture_output=True, text=True, timeout=15)
                devs = json.loads(r.stdout)
                return f"Found {len(devs)} devices"
            elif args == "on":
                subprocess.run(["termux-bt-enable", "on"], timeout=3)
                return "Bluetooth on"
            elif args == "off":
                subprocess.run(["termux-bt-enable", "off"], timeout=3)
                return "Bluetooth off"
            return "Bluetooth status"

        else:
            return f"Unknown tool: {tool}"

    except Exception as e:
        return f"Tool error: {e}"

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            tools_path = SCRIPT_DIR / "tools.json"
            tools = json.load(open(tools_path)) if tools_path.exists() else []
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "tools": tools}).encode())
        except: pass

    def do_POST(self):
        result = ""
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            msg = body.get("message", "").strip()
            print(f"USER: {msg}")

            # Step 1: Send to Mimo
            messages = [{"role": "user", "content": msg}]
            mimo_response = call_mimo(messages)
            print(f"MIMO: {mimo_response[:100]}")

            # Step 2: Check if Mimo wants a tool
            if "TOOL:" in mimo_response:
                # Extract tool call
                import re
                tool_match = re.search(r'TOOL:([^:\n]+):?([^\n]*)', mimo_response)
                if tool_match:
                    tool_name = tool_match.group(1).strip()
                    tool_args = tool_match.group(2).strip()

                    # Execute the tool
                    tool_result = execute_tool(f"{tool_name}:{tool_args}")
                    print(f"TOOL RESULT: {tool_result}")

                    # Send tool result back to Mimo
                    messages.append({"role": "assistant", "content": mimo_response})
                    messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
                    final_response = call_mimo(messages)
                    result = final_response
                else:
                    result = mimo_response
            else:
                result = mimo_response

            print(f"REPLY: {result[:80]}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": result}).encode())
        except Exception as e:
            print(f"ERR: {e}")
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"reply": f"Error: {e}"}).encode())
            except: pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *a): pass

subprocess.run(["termux-wake-lock"], timeout=3)
print(f"BruceClaw Bridge v8 at http://localhost:{PORT}")
FastServer(("0.0.0.0", PORT), H).serve_forever()
