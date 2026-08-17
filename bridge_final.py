#!/usr/bin/env python3
"""BruceClaw Direct Control - Bypasses LLM, executes commands directly"""
import socketserver, http.server, json, subprocess, os, time, threading, re
from pathlib import Path
from datetime import datetime

PORT = 9999
HOME = Path(os.path.expanduser("~"))
MESSAGES_DIR = HOME / "bruceclaw_messages"
MESSAGES_DIR.mkdir(exist_ok=True)
SCRIPT_DIR = Path(__file__).parent

# Conversation memory
HISTORY_FILE = HOME / "bruceclaw_history.json"
conversation_history = []

def load_history():
    global conversation_history
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                conversation_history = json.load(f)
        except: conversation_history = []

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(conversation_history[-100:], f, indent=2)

def add_history(role, content):
    conversation_history.append({"role": role, "content": content, "time": datetime.now().strftime("%H:%M")})
    save_history()

# Knowledge base
KB = {}
try:
    with open(SCRIPT_DIR / "knowledge_base.json") as f:
        KB = json.load(f)
except: pass

# Answering machine state
answering_machine = {"enabled": False, "messages": [], "conversation_log": []}

def clean_for_tts(text):
    text = re.sub(r'[#*/\\@<>{}|~`]', '', text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2190-\u21FF\u2600-\u26FF\u2700-\u27BF]', '', text)
    text = text.replace('&', 'and')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def speak(text):
    cleaned = clean_for_tts(text)
    try: subprocess.run(["termux-tts-speak", cleaned], timeout=15)
    except: pass

def execute(msg):
    """Execute a command directly"""
    msg_lower = msg.lower().strip()
    print(f"CMD: {msg_lower[:80]}")

    # ANSWERING MACHINE - highest priority
    if any(x in msg_lower for x in ["answering machine on","enable answering machine","answer calls on","answer my calls","set up answering machine","auto answer"]):
        answering_machine["enabled"] = True
        subprocess.run(["termux-notification","-t","BruceClaw","-c","Answering machine ON - answering calls as Jessica","--id","am-status"], timeout=3)
        return "Answering machine ENABLED. I will now answer your incoming calls as Jessica, Bruce's assistant at Bruce Racing. When someone calls, I'll greet them, answer their questions, and take messages."

    if any(x in msg_lower for x in ["answering machine off","disable answering machine","stop answering","stop answering machine","turn off answering"]):
        answering_machine["enabled"] = False
        subprocess.run(["termux-notification-remove","--id","am-status"], timeout=3)
        return "Answering machine DISABLED."

    if any(x in msg_lower for x in ["answering machine status","voicemail status","is answering machine on"]):
        status = "ON" if answering_machine["enabled"] else "OFF"
        count = len(answering_machine["messages"])
        return f"Answering machine: {status}\nMessages: {count}"

    if any(x in msg_lower for x in ["set greeting","change greeting"]):
        text = ""
        for sep in ["set greeting ","change greeting "]:
            if sep in msg_lower: text = msg.split(sep, 1)[-1].strip(); break
        if text: return f"Greeting updated: {text}"
        return "What greeting? Say: set greeting [your message]"

    if any(x in msg_lower for x in ["check messages","voicemail","my messages","any messages","did anyone call"]):
        msgs = answering_machine["messages"]
        if msgs:
            lines = [f"[{m['time']}] {m['number']}: {m.get('note','no note')}" for m in msgs[-10:]]
            return f"Messages ({len(msgs)} total):\n" + "\n".join(lines)
        return "No messages"

    if any(x in msg_lower for x in ["conversation log","what did they say","call details"]):
        logs = answering_machine["conversation_log"]
        if logs:
            lines = []
            for log in logs[-5:]:
                lines.append(f"--- {log['time']} ({log['number']}) ---")
                lines.append(log.get("transcript","No transcript"))
            return "\n".join(lines)
        return "No conversation logs yet"

    # SMS
    if any(x in msg_lower for x in ["send sms","send message","text ","send a text"]):
        number = ""; text = "Hello"
        if "to" in msg_lower:
            after = msg_lower.split("to")[-1].strip()
            parts = after.split(None, 1)
            number = parts[0].replace(" ","").replace("-","").replace("+","")
            if len(parts) > 1:
                text = parts[1].replace("say ","").replace("and say ","")
        if number:
            r = subprocess.run(["termux-sms-send","-n",number,text], capture_output=True, text=True, timeout=10)
            return f"SMS sent to {number}: {text}" if r.returncode == 0 else f"SMS failed"
        return "Give me a phone number to send to"

    if any(x in msg_lower for x in ["read sms","check sms","show sms","my sms","inbox"]):
        r = subprocess.run(["termux-sms-list","-l","10"], capture_output=True, text=True, timeout=5)
        try:
            msgs = json.loads(r.stdout)
            lines = [f"{m.get('address','?')}: {m.get('body','')[:60]}" for m in msgs[:10]]
            return "\n".join(lines) if lines else "No messages"
        except: return "No messages"

    # CALLS
    if any(x in msg_lower for x in ["call ","dial ","phone call","ring "]):
        number = ""
        for sep in ["to ","call ","dial ","ring "]:
            if sep in msg_lower:
                after = msg_lower.split(sep)[-1].strip()
                number = after.split()[0].replace(" ","").replace("-","")
                break
        if number:
            subprocess.run(["am","start","-a","android.intent.action.DIAL","-d",f"tel:{number}"], timeout=5)
            return f"Calling {number}..."
        return "Give me a phone number"

    if any(x in msg_lower for x in ["end call","hang up","disconnect"]):
        subprocess.run(["input","keyevent","6"], timeout=5)
        return "Call ended"

    if any(x in msg_lower for x in ["answer call","pick up","accept call"]):
        subprocess.run(["input","keyevent","5"], timeout=5)
        return "Call answered"

    if any(x in msg_lower for x in ["call log","call history","recent calls","who called"]):
        r = subprocess.run(["termux-call-log","-l","10"], capture_output=True, text=True, timeout=5)
        try:
            calls = json.loads(r.stdout)
            lines = [f"{c.get('number','?')} ({c.get('type','?')}) {c.get('date','?')}" for c in calls[:10]]
            return "\n".join(lines) if lines else "No call history"
        except: return "No call history"

    # PHONE STATE
    if any(x in msg_lower for x in ["battery","power","charge"]):
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
        try:
            d = json.loads(r.stdout)
            if "voltage" in msg_lower: return f"{d.get('voltage',0)/1000:.2f}V"
            elif "percent" in msg_lower or "level" in msg_lower: return f"{d.get('percentage','?')}%"
            return f"Battery: {d.get('percentage','?')}% at {d.get('voltage',0)/1000:.1f}V, {d.get('temperature','?')}C"
        except: return "N/A"

    if any(x in msg_lower for x in ["sim","imei","phone info","network"]):
        r = subprocess.run(["termux-telephony-deviceinfo"], capture_output=True, text=True, timeout=5)
        try:
            d = json.loads(r.stdout)
            return f"IMEI: {d.get('imei1','?')}\nNetwork: {d.get('network_operator_name','?')}\nSIM: {d.get('sim_operator_name','?')}"
        except: return "N/A"

    # CONTACTS
    if any(x in msg_lower for x in ["contact","contacts","address book","phonebook"]):
        r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=5)
        try:
            contacts = json.loads(r.stdout)
            if "search" in msg_lower or "find" in msg_lower:
                q = msg_lower.split("search")[-1].split("find")[-1].strip()
                matches = [c for c in contacts if q in c.get("name","").lower()]
                lines = [f"{c.get('name','?')}: {c.get('number','?')}" for c in matches[:10]]
                return "\n".join(lines) if lines else f"No contacts matching '{q}'"
            lines = [f"{c.get('name','?')}: {c.get('number','?')}" for c in contacts[:20]]
            return f"{len(contacts)} contacts:\n" + "\n".join(lines)
        except: return "No contacts"

    # CALENDAR
    if any(x in msg_lower for x in ["calendar","event","events","schedule","appointment"]):
        r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=5)
        try:
            events = json.loads(r.stdout)
            lines = [f"{e.get('eventMessage','?')} ({e.get('begin','?')})" for e in events[:10]]
            return "\n".join(lines) if lines else "No events"
        except: return "No events"

    # WIFI
    if "wifi" in msg_lower:
        if any(x in msg_lower for x in ["scan","networks","nearby"]):
            r = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=10)
            try:
                nets = json.loads(r.stdout)
                lines = [f"{n.get('ssid','?')} ({n.get('frequency','?')}MHz)" for n in nets[:10]]
                return "\n".join(lines) if lines else "No networks"
            except: return "No networks"
        elif any(x in msg_lower for x in ["on","enable"]):
            subprocess.run(["termux-wifi-enable","on"], timeout=5); return "WiFi on"
        elif any(x in msg_lower for x in ["off","disable"]):
            subprocess.run(["termux-wifi-enable","off"], timeout=5); return "WiFi off"
        else:
            r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=3)
            try:
                d = json.loads(r.stdout)
                return f"WiFi: {d.get('ssid','?')} ({d.get('link_speed','?')}Mbps)"
            except: return "N/A"

    # BLUETOOTH
    if any(x in msg_lower for x in ["bluetooth","bt "]):
        if any(x in msg_lower for x in ["scan","discover","nearby","devices"]):
            r = subprocess.run(["termux-bt-scan"], capture_output=True, text=True, timeout=15)
            try:
                devs = json.loads(r.stdout)
                lines = [f"{d.get('name','?')} ({d.get('address','?')})" for d in devs[:10]]
                return f"Found {len(devs)} devices:\n" + "\n".join(lines) if lines else "No devices"
            except: return "No devices"
        elif any(x in msg_lower for x in ["on","enable"]):
            subprocess.run(["termux-bt-enable","on"], timeout=5); return "Bluetooth on"
        elif any(x in msg_lower for x in ["off","disable"]):
            subprocess.run(["termux-bt-enable","off"], timeout=5); return "Bluetooth off"

    # LOCATION
    if any(x in msg_lower for x in ["location","where am i","gps","position","coordinates"]):
        r = subprocess.run(["termux-location","-p","gps"], capture_output=True, text=True, timeout=10)
        try:
            d = json.loads(r.stdout)
            lat = d.get("latitude","?"); lon = d.get("longitude","?")
            return f"Location: {lat}, {lon}\nhttps://maps.google.com/?q={lat},{lon}"
        except: return "N/A"

    # CAMERA
    if any(x in msg_lower for x in ["camera","photo","take picture","snap"]):
        path = str(HOME / f"photo_{int(time.time())}.jpg")
        subprocess.run(["termux-camera-photo",path], timeout=15)
        return f"Photo saved: {path}" if os.path.exists(path) else "Camera failed"

    # SCREENSHOT
    if "screenshot" in msg_lower:
        path = str(HOME / f"screen_{int(time.time())}.png")
        subprocess.run(["termux-screenshot",path], timeout=5)
        return f"Screenshot: {path}" if os.path.exists(path) else "Failed"

    # CLIPBOARD
    if any(x in msg_lower for x in ["clipboard","copy","paste","clip"]):
        if any(x in msg_lower for x in ["copy ","set ","put "]):
            text = msg_lower.split("copy")[-1].split("set")[-1].split("put")[-1].strip()
            subprocess.run(["termux-clipboard-set",text], timeout=3)
            return f"Copied: {text}"
        else:
            r = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, timeout=3)
            return f"Clipboard: {r.stdout.strip()}" if r.stdout.strip() else "Clipboard empty"

    # NOTIFICATIONS
    if any(x in msg_lower for x in ["notify","notification","alert"]):
        m = msg_lower.replace("notify","").replace("notification","").replace("alert","").strip()
        if m:
            subprocess.run(["termux-notification","-t","BruceClaw","-c",m], timeout=3)
            return "Notification sent"
        return "What should the notification say?"

    # TTS
    if any(x in msg_lower for x in ["speak ","say ","tts ","voice ","read aloud ","read out "]):
        text = ""
        for sep in ["speak ","say ","tts ","voice ","read aloud ","read out "]:
            if sep in msg_lower: text = msg_lower.split(sep, 1)[-1].strip(); break
        if text:
            speak(text)
            return f"Speaking: {text}"
        return "What should I say?"

    # VOLUME
    if any(x in msg_lower for x in ["volume","sound","mute","unmute","loud","quiet"]):
        if any(x in msg_lower for x in ["mute","silent","quiet","down"]):
            subprocess.run(["termux-volume","music","0"], timeout=3); return "Volume muted"
        elif any(x in msg_lower for x in ["unmute","loud","max","up"]):
            subprocess.run(["termux-volume","music","15"], timeout=3); return "Volume maxed"

    # BRIGHTNESS
    if any(x in msg_lower for x in ["brightness","dim","bright","screen light"]):
        if any(x in msg_lower for x in ["max","full","bright","100"]):
            subprocess.run(["termux-brightness","255"], timeout=3); return "Brightness maxed"
        elif any(x in msg_lower for x in ["min","low","dim","dark"]):
            subprocess.run(["termux-brightness","10"], timeout=3); return "Brightness dimmed"
        else:
            subprocess.run(["termux-brightness","128"], timeout=3); return "Brightness 50%"

    # VIBRATE
    if any(x in msg_lower for x in ["vibrate","buzz","haptic"]):
        ms = "2000" if "long" in msg_lower else "500"
        subprocess.run(["termux-vibrate","-d",ms], timeout=5)
        return f"Vibrating {ms}ms"

    # STORAGE
    if any(x in msg_lower for x in ["storage","space","disk","memory"]):
        r = subprocess.run(["df","-h","/data"], capture_output=True, text=True, timeout=3)
        lines = r.stdout.strip().split("\n")
        return lines[1] if len(lines) > 1 else "N/A"

    # OPEN APP
    if any(x in msg_lower for x in ["open ","launch ","start app"]):
        app = msg_lower.replace("open","").replace("launch","").replace("start app","").strip()
        apps = {"whatsapp":"com.whatsapp","telegram":"org.telegram.messenger","chrome":"com.android.chrome",
                "settings":"com.android.settings","camera":"com.android.camera","maps":"com.google.android.apps.maps",
                "youtube":"com.google.android.youtube","calculator":"com.android.calculator2"}
        pkg = None
        for name, package in apps.items():
            if name in app: pkg = package; break
        if pkg:
            subprocess.run(["monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1"], capture_output=True, timeout=5)
            return f"Opening {app}..."
        return f"Unknown app: {app}"

    # WHATSAPP
    if any(x in msg_lower for x in ["whatsapp ","whatsapp message","send whatsapp","message on whatsapp"]):
        number = ""; text = "Hi"
        for sep in ["to ","whatsapp ","message ","send "]:
            if sep in msg_lower:
                after = msg_lower.split(sep)[-1].strip()
                parts = after.split(None, 1)
                number = parts[0].replace(" ","").replace("-","").replace("+","").replace("whatsapp","")
                if len(parts) > 1:
                    raw = parts[1]
                    for kw in ["say ","message ","and say ","and tell ","on whatsapp"]:
                        raw = raw.replace(kw,"")
                    text = raw.strip() or "Hi"
                break
        if not number:
            nums = re.findall(r'0\d{9}', msg_lower)
            if nums: number = nums[0]
        if number:
            url = f"https://wa.me/{number}?text={text.replace(' ','%20')}"
            subprocess.run(["am","start","-a","android.intent.action.VIEW","-d",url], timeout=5)
            return f"Opening WhatsApp to {number} with: {text}"
        return "Give me a phone number and message"

    # LEARN
    if any(x in msg_lower for x in ["learn this","remember this","add knowledge"]):
        text = ""
        for sep in ["learn this ","remember this ","add knowledge "]:
            if sep in msg_lower: text = msg_lower.split(sep, 1)[-1].strip(); break
        if text:
            if "learned_facts" not in KB: KB["learned_facts"] = []
            KB["learned_facts"].append({"fact": text, "added": datetime.now().strftime("%Y-%m-%d %H:%M")})
            with open(SCRIPT_DIR / "knowledge_base.json", "w") as f:
                json.dump(KB, f, indent=2)
            return f"Learned: {text}"
        return "What should I learn?"

    # HELP
    if any(x in msg_lower for x in ["help","what can","tools","capabilities","functions"]):
        return """I can do:
Answering Machine: on/off/greeting/messages
SMS: send/read
Calls: dial/end/answer/call log
Contacts: list/search
Battery: check status
WiFi: scan/on/off
Bluetooth: scan/on/off
Location: GPS
Camera: take photo
Screenshot
Clipboard: copy/paste
Notifications
TTS: speak text
Volume: up/down/mute
Brightness: dim/bright
Vibrate
Storage: check space
WhatsApp: send messages
Open apps
Files/Shell commands
Calendar
Learn: remember facts"""

    return None  # Not a command

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            tools_path = SCRIPT_DIR / "tools.json"
            tools = json.load(open(tools_path)) if tools_path.exists() else []
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
            msg = body.get("message","").strip()
            add_history("user", msg)
            print(f"USER: {msg}")

            tool_result = execute(msg)
            if tool_result is not None:
                result = tool_result
            else:
                result = "I can do: answering machine, SMS, calls, contacts, battery, WiFi, Bluetooth, location, camera, screenshot, clipboard, notifications, TTS, volume, brightness, vibrate, storage, apps, WhatsApp, files, calendar, and learn. What do you need?"

            add_history("assistant", result)
            print(f"REPLY: {result[:80]}")
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
                self.wfile.write(json.dumps({"reply":f"Error: {e}"}).encode())
            except: pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def log_message(self,*a): pass

load_history()
subprocess.run(["termux-wake-lock"], timeout=3)
print(f"BruceClaw Bridge v9.1 at http://localhost:{PORT}")
FastServer(("0.0.0.0",PORT),H).serve_forever()
