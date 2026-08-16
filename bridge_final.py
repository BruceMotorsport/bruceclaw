#!/usr/bin/env python3
"""BruceClaw Bridge v5 - ALL functions + Answering Machine"""
import socketserver, http.server, json, subprocess, os, time, threading
from pathlib import Path

PORT = 9999
HOME = Path(os.path.expanduser("~"))
MESSAGES_DIR = HOME / "bruceclaw_messages"
MESSAGES_DIR.mkdir(exist_ok=True)

# Answering machine state
answering_machine = {
    "enabled": False,
    "greeting": "Hello, Bruce is unavailable right now. Please leave your name, number, and message after the beep. I'll get back to you soon.",
    "max_wait": 30,
    "messages": []
}

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            tools = ["sms","send_sms","read_sms","call","dial","end_call",
                     "call_log","contacts","battery","wifi","bluetooth",
                     "location","camera","screenshot","clipboard","notify",
                     "tts","volume","brightness","vibrate","ringtone",
                     "storage","install","files","shell","calendar",
                     "open_app","wallpaper","media","screen",
                     "answering_machine","voicemail","messages"]
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
            msg = body.get("message","").lower().strip()
            print(f"REQ: {msg[:80]}")

            # ======== SMS ========
            if any(x in msg for x in ["send sms","send message","text ","send a text"]):
                number = ""
                text = "Hello"
                if "to" in msg:
                    after = msg.split("to")[-1].strip()
                    parts = after.split(None, 1)
                    number = parts[0].replace(" ","").replace("-","").replace("+","")
                    if len(parts) > 1:
                        text = parts[1].replace("say ","").replace("and say ","").replace("and tell ","")
                if number:
                    r = subprocess.run(["termux-sms-send","-n",number,text], capture_output=True, text=True, timeout=10)
                    if r.returncode == 0:
                        result = f"SMS sent to {number}: {text}"
                    else:
                        result = f"SMS failed: {r.stderr.strip() or r.stdout.strip()}"
                else:
                    result = "Give me a phone number to send to"

            elif any(x in msg for x in ["read sms","check sms","show sms","my sms","inbox","messages"]):
                limit = "10"
                r = subprocess.run(["termux-sms-list","-l",limit], capture_output=True, text=True, timeout=5)
                try:
                    msgs = json.loads(r.stdout)
                    lines = [f"{m.get('address','?')}: {m.get('body','')[:60]}" for m in msgs[:10]]
                    result = "\n".join(lines) if lines else "No messages"
                except:
                    result = r.stdout or "No messages"

            # ======== PHONE CALLS ========
            elif any(x in msg for x in ["call ","dial ","phone call","ring "]):
                number = ""
                for sep in ["to ","call ","dial ","ring "]:
                    if sep in msg:
                        after = msg.split(sep)[-1].strip()
                        number = after.split()[0].replace(" ","").replace("-","")
                        break
                if number:
                    subprocess.run(["am","start","-a","android.intent.action.DIAL","-d",f"tel:{number}"], capture_output=True, text=True, timeout=5)
                    result = f"Calling {number}..."
                else:
                    result = "Give me a phone number to call"

            elif any(x in msg for x in ["end call","hang up","disconnect","stop call"]):
                subprocess.run(["input","keyevent","6"], timeout=5)
                result = "Call ended"

            elif any(x in msg for x in ["answer call","pick up","accept call"]):
                subprocess.run(["input","keyevent","5"], timeout=5)
                result = "Call answered"

            elif any(x in msg for x in ["reject call","decline call","deny call"]):
                subprocess.run(["input","keyevent","6"], timeout=5)
                result = "Call rejected"

            elif any(x in msg for x in ["call log","call history","recent calls","who called"]):
                r = subprocess.run(["termux-call-log","-l","10"], capture_output=True, text=True, timeout=5)
                try:
                    calls = json.loads(r.stdout)
                    lines = [f"{c.get('number','?')} ({c.get('type','?')}) {c.get('date','?')}" for c in calls[:10]]
                    result = "\n".join(lines) if lines else "No call history"
                except:
                    result = r.stdout or "No call history"

            # ======== PHONE STATE ========
            elif any(x in msg for x in ["battery","power","charge"]):
                r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=3)
                try:
                    d = json.loads(r.stdout)
                    if "voltage" in msg:
                        result = f"{d.get('voltage',0)/1000:.2f}V"
                    elif "percent" in msg or "level" in msg or "how much" in msg:
                        result = f"{d.get('percentage','?')}%"
                    else:
                        result = f"Battery: {d.get('percentage','?')}% at {d.get('voltage',0)/1000:.1f}V, {d.get('temperature','?')}C"
                except:
                    result = r.stdout or "N/A"

            elif any(x in msg for x in ["sim","imei","phone number","phone info","network"]):
                r = subprocess.run(["termux-telephony-deviceinfo"], capture_output=True, text=True, timeout=5)
                try:
                    d = json.loads(r.stdout)
                    result = f"IMEI: {d.get('imei1','?')}\nNetwork: {d.get('network_operator_name','?')}\nSIM: {d.get('sim_operator_name','?')}"
                except:
                    result = r.stdout or "N/A"

            elif any(x in msg for x in ["cell info","signal","cellular"]):
                r = subprocess.run(["termux-telephony-cellinfo"], capture_output=True, text=True, timeout=5)
                try:
                    info = json.loads(r.stdout)
                    result = json.dumps(info, indent=2)[:500]
                except:
                    result = r.stdout or "N/A"

            # ======== CONTACTS ========
            elif any(x in msg for x in ["contact","contacts","address book","phonebook"]):
                r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=5)
                try:
                    contacts = json.loads(r.stdout)
                    if "search" in msg or "find" in msg:
                        q = msg.split("search")[-1].split("find")[-1].strip()
                        matches = [c for c in contacts if q in c.get("name","").lower()]
                        lines = [f"{c.get('name','?')}: {c.get('number','?')}" for c in matches[:10]]
                        result = "\n".join(lines) if lines else f"No contacts matching '{q}'"
                    else:
                        lines = [f"{c.get('name','?')}: {c.get('number','?')}" for c in contacts[:20]]
                        result = f"{len(contacts)} contacts:\n" + "\n".join(lines)
                except:
                    result = r.stdout or "No contacts"

            # ======== CALENDAR ========
            elif any(x in msg for x in ["calendar","event","events","schedule","appointment"]):
                r = subprocess.run(["termux-calendar-list"], capture_output=True, text=True, timeout=5)
                try:
                    events = json.loads(r.stdout)
                    lines = [f"{e.get('eventMessage','?')} ({e.get('begin','?')})" for e in events[:10]]
                    result = "\n".join(lines) if lines else "No events"
                except:
                    result = r.stdout or "No events"

            # ======== WIFI ========
            elif "wifi" in msg:
                if any(x in msg for x in ["scan","available","networks","nearby"]):
                    r = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=10)
                    try:
                        nets = json.loads(r.stdout)
                        lines = [f"{n.get('ssid','?')} ({n.get('frequency','?')}MHz)" for n in nets[:10]]
                        result = "\n".join(lines) if lines else "No networks found"
                    except:
                        result = r.stdout or "No networks"
                elif any(x in msg for x in ["on","enable","connect"]):
                    subprocess.run(["termux-wifi-enable","on"], timeout=5)
                    result = "WiFi enabled"
                elif any(x in msg for x in ["off","disable"]):
                    subprocess.run(["termux-wifi-enable","off"], timeout=5)
                    result = "WiFi disabled"
                else:
                    r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=3)
                    try:
                        d = json.loads(r.stdout)
                        result = f"WiFi: {d.get('ssid','?')} ({d.get('link_speed','?')}Mbps)"
                    except:
                        result = r.stdout or "N/A"

            # ======== BLUETOOTH ========
            elif any(x in msg for x in ["bluetooth","bt "]):
                if any(x in msg for x in ["scan","discover","find","nearby","devices"]):
                    r = subprocess.run(["termux-bt-scan"], capture_output=True, text=True, timeout=15)
                    try:
                        devs = json.loads(r.stdout)
                        lines = [f"{d.get('name','?')} ({d.get('address','?')})" for d in devs[:10]]
                        result = f"Found {len(devs)} devices:\n" + "\n".join(lines) if lines else "No devices found"
                    except:
                        result = r.stdout or "No devices"
                elif any(x in msg for x in ["on","enable"]):
                    subprocess.run(["termux-bt-enable","on"], timeout=5)
                    result = "Bluetooth enabled"
                elif any(x in msg for x in ["off","disable"]):
                    subprocess.run(["termux-bt-enable","off"], timeout=5)
                    result = "Bluetooth disabled"
                else:
                    r = subprocess.run(["termux-bt-info"], capture_output=True, text=True, timeout=5)
                    try:
                        d = json.loads(r.stdout)
                        result = f"BT: {d.get('enabled','?')}, MAC: {d.get('address','?')}"
                    except:
                        result = r.stdout or "N/A"

            # ======== LOCATION ========
            elif any(x in msg for x in ["location","where am i","gps","position","coordinates","map"]):
                r = subprocess.run(["termux-location","-p","gps"], capture_output=True, text=True, timeout=10)
                try:
                    d = json.loads(r.stdout)
                    lat = d.get("latitude","?")
                    lon = d.get("longitude","?")
                    result = f"Location: {lat}, {lon}\nhttps://maps.google.com/?q={lat},{lon}"
                except:
                    result = r.stdout or "N/A"

            # ======== CAMERA ========
            elif any(x in msg for x in ["camera","photo","take picture","snap"]):
                path = str(HOME / f"photo_{int(time.time())}.jpg")
                r = subprocess.run(["termux-camera-photo",path], capture_output=True, text=True, timeout=15)
                if os.path.exists(path):
                    result = f"Photo saved: {path}"
                else:
                    result = f"Camera failed: {r.stderr.strip()}"

            # ======== SCREENSHOT ========
            elif "screenshot" in msg:
                path = str(HOME / f"screen_{int(time.time())}.png")
                r = subprocess.run(["termux-screenshot",path], capture_output=True, text=True, timeout=5)
                if os.path.exists(path):
                    result = f"Screenshot saved: {path}"
                else:
                    result = f"Screenshot failed: {r.stderr.strip()}"

            # ======== CLIPBOARD ========
            elif any(x in msg for x in ["clipboard","copy","paste","clip"]):
                if any(x in msg for x in ["copy ","set ","put "]):
                    text = msg.split("copy")[-1].split("set")[-1].split("put")[-1].strip()
                    subprocess.run(["termux-clipboard-set",text], timeout=3)
                    result = f"Copied: {text}"
                else:
                    r = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, timeout=3)
                    result = f"Clipboard: {r.stdout.strip()}" if r.stdout.strip() else "Clipboard empty"

            # ======== NOTIFICATIONS ========
            elif any(x in msg for x in ["notify","notification","alert"]):
                m = msg.replace("notify","").replace("notification","").replace("alert","").strip()
                if m:
                    subprocess.run(["termux-notification","-t","BruceClaw","-c",m], timeout=3)
                    result = "Notification sent"
                else:
                    result = "What should the notification say?"

            elif any(x in msg for x in ["dismiss notification","clear notification"]):
                subprocess.run(["termux-notification-remove","-t","BruceClaw"], timeout=3)
                result = "Notification dismissed"

            # ======== TTS ========
            elif any(x in msg for x in ["speak","say ","tts","voice","read aloud","read out"]):
                text = ""
                for sep in ["speak ","say ","tts ","voice ","read aloud ","read out "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    subprocess.run(["termux-tts-speak",text], timeout=10)
                    result = f"Speaking: {text}"
                else:
                    result = "What should I say?"

            # ======== VOLUME ========
            elif any(x in msg for x in ["volume","sound","mute","unmute","loud","quiet"]):
                if any(x in msg for x in ["mute","silent","quiet","down"]):
                    subprocess.run(["termux-volume","music","0"], timeout=3)
                    result = "Volume muted"
                elif any(x in msg for x in ["unmute","loud","max","up"]):
                    subprocess.run(["termux-volume","music","15"], timeout=3)
                    result = "Volume maxed"
                else:
                    r = subprocess.run(["termux-volume"], capture_output=True, text=True, timeout=3)
                    result = r.stdout or "N/A"

            # ======== BRIGHTNESS ========
            elif any(x in msg for x in ["brightness","dim","bright","screen light"]):
                if any(x in msg for x in ["max","full","bright","100"]):
                    subprocess.run(["termux-brightness","255"], timeout=3)
                    result = "Brightness maxed"
                elif any(x in msg for x in ["min","low","dim","dark"]):
                    subprocess.run(["termux-brightness","10"], timeout=3)
                    result = "Brightness dimmed"
                else:
                    subprocess.run(["termux-brightness","128"], timeout=3)
                    result = "Brightness set to 50%"

            # ======== VIBRATE ========
            elif any(x in msg for x in ["vibrate","buzz","haptic"]):
                ms = "2000" if "long" in msg else "500"
                subprocess.run(["termux-vibrate","-d",ms], timeout=5)
                result = f"Vibrating for {ms}ms"

            # ======== RINGTONE ========
            elif any(x in msg for x in ["ringtone","alarm ring","play alarm"]):
                subprocess.run(["termux-media-player","play","-t","alarm"], timeout=5)
                result = "Playing alarm tone"

            # ======== STORAGE ========
            elif any(x in msg for x in ["storage","space","disk"]):
                r = subprocess.run(["df","-h","/data"], capture_output=True, text=True, timeout=3)
                lines = r.stdout.strip().split("\n")
                result = lines[1] if len(lines) > 1 else "N/A"

            # ======== OPEN APP ========
            elif any(x in msg for x in ["open ","launch ","start app"]):
                app = msg.replace("open","").replace("launch","").replace("start app","").strip()
                apps = {
                    "whatsapp":"com.whatsapp","telegram":"org.telegram.messenger",
                    "chrome":"com.android.chrome","settings":"com.android.settings",
                    "phone":"com.android.dialer","messages":"com.android.messaging",
                    "camera":"com.android.camera","gallery":"com.android.gallery3d",
                    "maps":"com.google.android.apps.maps","youtube":"com.google.android.youtube",
                    "play store":"com.android.vending","calculator":"com.android.calculator2",
                    "clock":"com.android.deskclock","contacts":"com.android.contacts",
                    "files":"com.google.android.apps.nbu.files"
                }
                pkg = None
                for name, package in apps.items():
                    if name in app:
                        pkg = package
                        break
                if pkg:
                    subprocess.run(["monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1"], capture_output=True, text=True, timeout=5)
                    result = f"Opening {app}..."
                else:
                    result = f"Unknown app '{app}'. Try: whatsapp, telegram, chrome, settings, camera, phone, maps, youtube"

            # ======== FILES ========
            elif any(x in msg for x in ["file","ls ","list files","directory"]):
                path = str(HOME)
                r = subprocess.run(["ls","-la",path], capture_output=True, text=True, timeout=5)
                result = r.stdout[:800] or "Empty"

            # ======== SHELL ========
            elif any(x in msg for x in ["run ","execute ","terminal ","shell ","command "]):
                cmd = msg
                for sep in ["run ","execute ","terminal ","shell ","command "]:
                    if sep in msg:
                        cmd = msg.split(sep, 1)[-1].strip()
                        break
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                result = (r.stdout or r.stderr or "Done")[:800]

            # ======== SCREEN ========
            elif any(x in msg for x in ["screen on","screen off","turn on screen","turn off screen","lock screen"]):
                if any(x in msg for x in ["on","wake"]):
                    subprocess.run(["termux-wake-lock"], timeout=3)
                    result = "Screen on"
                else:
                    subprocess.run(["input","keyevent","26"], timeout=3)
                    result = "Screen off"

            # ======== MEDIA ========
            elif any(x in msg for x in ["play music","play song","music","pause","stop music"]):
                if any(x in msg for x in ["pause","stop","halt"]):
                    subprocess.run(["termux-media-player","pause"], timeout=3)
                    result = "Music paused"
                else:
                    subprocess.run(["termux-media-player","play","-t","music"], timeout=3)
                    result = "Playing music"

            # ======== INSTALL ========
            elif "install" in msg:
                pkg = msg.replace("install","").strip()
                subprocess.run(["pkg","install","-y",pkg], capture_output=True, text=True, timeout=60)
                result = f"{pkg} installed"

            # ======== ANSWERING MACHINE ========
            elif any(x in msg for x in ["answering machine on","enable answering machine","voicemail on","answer calls on"]):
                answering_machine["enabled"] = True
                subprocess.run(["termux-notification","-t","BruceClaw","-c","Answering machine ON - calls will be auto-answered","--id","am-status"], timeout=3)
                result = "Answering machine ENABLED. Incoming calls will be auto-answered with your greeting."

            elif any(x in msg for x in ["answering machine off","disable answering machine","voicemail off","answer calls off","stop answering"]):
                answering_machine["enabled"] = False
                subprocess.run(["termux-notification-remove","--id","am-status"], timeout=3)
                result = "Answering machine DISABLED."

            elif any(x in msg for x in ["set greeting","change greeting","record greeting","set voicemail message"]):
                text = ""
                for sep in ["set greeting ","change greeting ","record greeting ","set voicemail message "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    answering_machine["greeting"] = text
                    result = f"Greeting updated: {text}"
                else:
                    result = f"Current greeting: {answering_machine['greeting']}\n\nTo change, say: set greeting [your message]"

            elif any(x in msg for x in ["answering machine status","voicemail status","is answering machine on"]):
                status = "ON" if answering_machine["enabled"] else "OFF"
                count = len(answering_machine["messages"])
                result = f"Answering machine: {status}\nGreeting: {answering_machine['greeting'][:80]}...\nMessages: {count}"

            elif any(x in msg for x in ["check messages","voicemail","my messages","any messages","did anyone call"]):
                msgs = answering_machine["messages"]
                if msgs:
                    lines = []
                    for m in msgs[-10:]:
                        lines.append(f"[{m['time']}] {m['number']}: {m.get('note','no note')}")
                    result = f"Messages ({len(msgs)} total):\n" + "\n".join(lines)
                else:
                    result = "No messages"

            elif any(x in msg for x in ["clear messages","delete messages","clear voicemail"]):
                answering_machine["messages"] = []
                for f in MESSAGES_DIR.glob("call_*.json"):
                    f.unlink()
                result = "All messages cleared"

            elif any(x in msg for x in ["add note","note for","caller note"]):
                text = msg.replace("add note","").replace("note for","").replace("caller note","").strip()
                if answering_machine["messages"]:
                    answering_machine["messages"][-1]["note"] = text
                    result = f"Note added to last message: {text}"
                else:
                    result = "No messages to add a note to"

            # ======== HELP ========
            elif any(x in msg for x in ["help","what can","tools","capabilities","functions"]):
                result = """SMS: send/read
Calls: dial/end/answer/reject/call log
Contacts: list/search
Battery: level/voltage/health
WiFi: status/scan/on/off
Bluetooth: info/scan/on/off
Location: GPS
Camera: photo
Screenshot
Clipboard: copy/paste
Notifications
TTS: speak
Volume: up/down/mute
Brightness: dim/bright
Vibrate
Storage: space
Open apps
Files/Shell
Calendar/Events
Answering Machine: on/off/greeting/messages"""

            else:
                result = "I can do: SMS, calls, contacts, battery, WiFi, Bluetooth, location, camera, screenshot, clipboard, notifications, TTS, volume, brightness, vibrate, storage, apps, files, calendar. What do you need?"

            print(f"RES: {result[:80]}")
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
                self.wfile.write(json.dumps({"reply":f"Error: {str(e)}"}).encode())
            except: pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def log_message(self,*a): pass


def call_monitor():
    """Background thread - monitors incoming calls when answering machine is ON"""
    last_state = "idle"
    while True:
        time.sleep(3)
        if not answering_machine["enabled"]:
            last_state = "idle"
            continue
        try:
            r = subprocess.run(["termux-telephony-deviceinfo"], capture_output=True, text=True, timeout=3)
            # Check call state via dumpsys
            r2 = subprocess.run(["dumpsys","telephony.registry"], capture_output=True, text=True, timeout=3)
            state_line = [l for l in r2.stdout.split("\n") if "mCallState" in l]
            if state_line:
                call_state = state_line[0].strip()
                if "mCallState=2" in call_state and last_state != "ringing":
                    # Incoming call detected - answer it
                    last_state = "ringing"
                    print("INCOMING CALL DETECTED - Answering...")
                    subprocess.run(["input","keyevent","5"], timeout=5)  # Answer
                    time.sleep(2)
                    # Play greeting via TTS
                    subprocess.run(["termux-tts-speak", answering_machine["greeting"]], timeout=15)
                    # Beep sound
                    subprocess.run(["termux-tts-speak","Beep"], timeout=3)
                    # Wait for caller to leave message
                    time.sleep(answering_machine["max_wait"])
                    # Hang up
                    subprocess.run(["input","keyevent","6"], timeout=5)
                    # Log the call
                    from datetime import datetime
                    msg = {
                        "number": "unknown",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "note": "auto-answered, greeting played",
                        "duration": answering_machine["max_wait"]
                    }
                    answering_machine["messages"].append(msg)
                    # Save to file
                    fname = MESSAGES_DIR / f"call_{int(time.time())}.json"
                    with open(fname, "w") as f:
                        json.dump(msg, f)
                    # Notify Bruce
                    subprocess.run(["termux-notification","-t","BruceClaw","-c",f"Missed call logged from {msg['number']} at {msg['time']}","--id","am-call"], timeout=3)
                    last_state = "idle"
                elif "mCallState=0" in call_state:
                    last_state = "idle"
        except:
            last_state = "idle"


# Start call monitor thread
monitor = threading.Thread(target=call_monitor, daemon=True)
monitor.start()

print(f"BruceClaw Bridge v5 at http://localhost:{PORT}")
FastServer(("0.0.0.0",PORT),H).serve_forever()
