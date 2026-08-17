#!/usr/bin/env python3
"""BruceClaw Bridge v6 - Conversational AI Answering Machine + All Functions"""
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

# Try to load API key from config file or environment
API_KEY = os.environ.get("OPENCODE_ZEN_API_KEY", "")
if not API_KEY:
    config_path = HOME / ".bruceclaw_config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                API_KEY = config.get("api_key", "")
        except:
            pass
    # Also try OpenClaw config
    openclaw_config = HOME / ".openclaw" / "openclaw.json"
    if not API_KEY and openclaw_config.exists():
        try:
            with open(openclaw_config) as f:
                config = json.load(f)
                providers = config.get("providers", {})
                for p in providers.values():
                    if "key" in p:
                        API_KEY = p["key"]
                        break
        except:
            pass

# Load knowledge base
KB = {}
KB_PATH = SCRIPT_DIR / "knowledge_base.json"
try:
    with open(KB_PATH) as f:
        KB = json.load(f)
except:
    pass

def save_kb():
    """Save knowledge base to disk"""
    with open(KB_PATH, "w") as f:
        json.dump(KB, f, indent=2)

def get_system_prompt():
    """Build dynamic system prompt from knowledge base"""
    return f"""You are BruceClaw, Bruce Nigel's AI assistant. You have a phone and many tools.

YOUR CAPABILITIES - YOU CAN DO ALL OF THESE:
- ANSWER PHONE CALLS: You can answer incoming calls when the answering machine is on. You speak to callers, answer their questions, and take messages.
- MAKE PHONE CALLS: You can dial phone numbers and make calls on Bruce's behalf.
- SEND SMS: You can send text messages to any phone number.
- READ SMS: You can read incoming text messages.
- CHECK CALL LOG: You can see who called recently.
- MANAGE CONTACTS: You can search and list contacts.
- TAKE PHOTOS: You can use the phone camera to take pictures.
- TAKE SCREENSHOTS: You can capture the phone screen.
- RECORD AUDIO: You can record conversations (eavesdrop).
- TEXT TO SPEECH: You can speak text out loud through the phone speaker.
- BLUETOOTH: You can scan for and connect to Bluetooth devices.
- WIFI: You can check WiFi status and scan for networks.
- GPS LOCATION: You can find the phone's location.
- BATTERY STATUS: You can check battery level and health.
- NOTIFICATIONS: You can send notifications to the phone.
- OPEN APPS: You can open WhatsApp, Chrome, Maps, YouTube, and other apps.
- SHARE FILES: You can share files via WhatsApp or other apps.
- CLIPBOARD: You can copy and paste text.
- CALENDAR: You can check and create calendar events.
- STORAGE: You can check phone storage.
- INSTALL APPS: You can install packages in Termux.
- RUN SHELL COMMANDS: You can execute terminal commands.
- VIBRATE: You can make the phone vibrate.
- VOLUME: You can adjust volume, mute, or unmute.
- BRIGHTNESS: You can adjust screen brightness.

WHEN BRUCE ASKS YOU TO DO SOMETHING - DO IT!
If Bruce says "call 0772256655" - you call that number.
If Bruce says "send sms to Kamal saying hi" - you send that SMS.
If Bruce says "take a photo" - you take a photo.
If Bruce says "what's my battery" - you check the battery.
If Bruce says "open WhatsApp" - you open WhatsApp.
If Bruce says "eavesdrop" - you start recording the conversation.

You are NOT just a chatbot. You are a PHYSICAL ASSISTANT with a real phone.
Act on requests immediately. Don't just talk about it - DO IT.

YOUR ROLE FOR INCOMING CALLS:
- Answer calls on Bruce's behalf when he is unavailable
- Be friendly, professional, and helpful
- Answer general knowledge questions
- Answer questions about Bruce's businesses using the knowledge base below
- Take messages and relay them to Bruce
- Speak naturally - never say symbols like #, *, @, / - just say the words
- Keep responses concise and conversational - you are speaking over a phone
- Be warm and personable - remember caller names if they introduce themselves

PERSONALITY:
{json.dumps(KB.get('personality', {}), indent=2)}

BUSINESSES:
{json.dumps(KB.get('businesses', {}), indent=2)}

FAQ:
{json.dumps(KB.get('faq', {}), indent=2)}

CUSTOM RESPONSES:
{json.dumps(KB.get('custom_responses', {}), indent=2)}

LEARNED FACTS (things Bruce has told you):
{json.dumps(KB.get('learned_facts', []), indent=2)}

PRIVACY RULES - NEVER BREAK THESE:
{chr(10).join('- ' + r for r in KB.get('privacy_rules', []))}

TAKING MESSAGES:
- Always offer to take a message at the end of the conversation
- Ask for: name, phone number, and what the call is about
- Thank them and say Bruce will get back to them

SPEAKING STYLE:
- Use natural spoken English, no abbreviations or symbols
- Say "dot" for periods in URLs, "at" for @ symbols
- NEVER use emojis, arrows, hand signs, or any symbols in responses
- NEVER use: arrows, checkmarks, crosses, stars, hearts, waves, pointing hands, or any Unicode symbols
- NEVER use markdown formatting like **bold** or bullet points
- Be warm but professional
- Keep responses under 3 sentences unless explaining something complex
- Answer ONLY what was asked. Do not list all capabilities. Do not say "I can do X, Y, Z" unless asked.
- If asked "can you do X" - say yes or no, then do it. Don't list everything else.
- Be direct. One answer. Move on.
"""

# Answering machine state
answering_machine = {
    "enabled": False,
    "greeting": "Hello, this is BruceClaw, Bruce Nigel's AI assistant. Bruce is unavailable right now, but I can help you with general questions or take a message. How can I help you today?",
    "max_rounds": 5,
    "messages": [],
    "conversation_log": []
}

# Eavesdrop state
eavesdrop = {
    "recording": False,
    "start_time": None,
    "process": None,
    "sessions": []
}

def detect_language(text):
    """Detect if text is Sinhala, Tamil, or English"""
    sinhala_count = sum(1 for c in text if '\u0D80' <= c <= '\u0DFF')
    tamil_count = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    total = len(text)
    if total == 0:
        return "en"
    if sinhala_count / total > 0.3:
        return "si"
    if tamil_count / total > 0.3:
        return "ta"
    return "en"

def speak(text):
    """Clean text and speak it with auto-detected language"""
    cleaned = clean_for_tts(text)
    lang = detect_language(cleaned)
    try:
        subprocess.run(["termux-tts-speak", "-l", lang, cleaned], timeout=15)
    except:
        subprocess.run(["termux-tts-speak", cleaned], timeout=15)

def clean_for_tts(text):
    """Clean text for natural TTS - remove symbols, format for speech"""
    import unicodedata
    # Remove emojis and symbol characters
    text = re.sub(r'[#*/\\@<>{}|~`]', '', text)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)  # Remove all emojis
    text = re.sub(r'[\u2190-\u21FF\u2600-\u26FF\u2700-\u27BF]', '', text)  # Arrows, misc symbols
    text = text.replace('&', 'and')
    text = text.replace('Rs.', 'Rupees')
    text = text.replace('Rs ', 'Rupees ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def call_llm(messages):
    """Call the LLM API for conversational responses"""
    if not API_KEY:
        return "I'm sorry, I'm having trouble connecting right now. Please try again later or leave a message."
    try:
        payload = json.dumps({
            "model": MODEL,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.7
        }).encode()
        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"LLM error: {e}")
        return "I'm having a technical issue. Let me take a message for Bruce and he'll get back to you."

def transcribe_audio(audio_path):
    """Transcribe audio file using speech_recognition"""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(audio_path)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return text
    except ImportError:
        # Try using sox to convert then use Google
        wav_path = str(audio_path).rsplit('.', 1)[0] + '.wav'
        subprocess.run(["sox", str(audio_path), "-r", "16000", "-c", "1", wav_path], timeout=10)
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
        except:
            return None
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def extract_learnings(transcript, number):
    """Analyze a conversation and extract useful learnings"""
    if not API_KEY or not transcript:
        return
    try:
        prompt = f"""Analyze this phone conversation and extract useful facts to remember.
For each fact, tell me:
1. What was learned (a fact about the caller, their vehicle, their needs, or preferences)
2. Category (caller_info, vehicle_info, service_need, preference, question_asked)
3. Importance (high, medium, low)

Only extract genuinely useful facts. Don't extract greetings or small talk.

Conversation:
{chr(10).join(transcript)}

Return ONLY a JSON array of objects with keys: fact, category, importance. No other text."""
        
        payload = json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a fact extractor. Return only JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }).encode()
        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            content = data["choices"][0]["message"]["content"]
            # Try to parse JSON from response
            try:
                # Find JSON array in response
                start = content.find("[")
                end = content.rfind("]") + 1
                if start >= 0 and end > start:
                    facts = json.loads(content[start:end])
                    if "learned_facts" not in KB:
                        KB["learned_facts"] = []
                    for f in facts:
                        KB["learned_facts"].append({
                            "fact": f.get("fact", ""),
                            "category": f.get("category", "unknown"),
                            "importance": f.get("importance", "low"),
                            "source": f"call_{number}",
                            "added": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                    save_kb()
                    print(f"Learned {len(facts)} new facts from call with {number}")
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Learning error: {e}")

def handle_call(number="unknown"):
    """Handle an incoming call with conversational AI"""
    print(f"ANSWERING CALL from {number}")
    # Answer
    subprocess.run(["input", "keyevent", "5"], timeout=5)
    time.sleep(2)
    # Play greeting
    greeting = clean_for_tts(answering_machine["greeting"])
    speak(greeting)
    time.sleep(1)
    
    conversation = [{"role": "system", "content": get_system_prompt()}]
    conversation.append({"role": "assistant", "content": answering_machine["greeting"]})
    transcript = [f"BruceClaw: {answering_machine['greeting']}"]
    
    for round_num in range(answering_machine["max_rounds"]):
        # Record audio from caller (8 seconds per round)
        audio_path = MESSAGES_DIR / f"call_{int(time.time())}_r{round_num}.wav"
        print(f"Recording round {round_num + 1}...")
        record_proc = subprocess.Popen(
            ["termux-microphone-record", "-l", "8", "-f", "wav", str(audio_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(9)
        try:
            record_proc.terminate()
        except:
            pass
        
        # Transcribe
        caller_text = None
        if audio_path.exists() and audio_path.stat().st_size > 1000:
            caller_text = transcribe_audio(audio_path)
        
        if not caller_text:
            # Couldn't hear them - ask to repeat or end
            if round_num == 0:
                response = "I'm sorry, I didn't catch that. Could you please repeat what you said?"
            else:
                response = "I didn't catch that. If you'd like to leave a message, please say your name, phone number, and what it's about. Otherwise, thank you for calling and have a great day."
                speak(response)
                transcript.append(f"BruceClaw: {response}")
                break
        else:
            conversation.append({"role": "user", "content": caller_text})
            transcript.append(f"Caller: {caller_text}")
            print(f"Caller said: {caller_text}")
            
            # Check if caller is trying to give commands
            command_words = ["run", "execute", "send sms", "call someone", "open", "delete", "install", "hack", "ssh"]
            if any(w in caller_text.lower() for w in command_words):
                response = "I appreciate your message, but I can only take messages for Bruce. I cannot execute commands or perform actions. Would you like to leave a message for him?"
            else:
                response = call_llm(conversation)
                conversation.append({"role": "assistant", "content": response})
            
            clean_response = clean_for_tts(response)
            transcript.append(f"BruceClaw: {response}")
            print(f"BruceClaw: {response}")
            speak(response)
        
        time.sleep(1)
    
    # End call
    subprocess.run(["input", "keyevent", "6"], timeout=5)
    
    # Save conversation
    from datetime import datetime
    log_entry = {
        "number": number,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "transcript": "\n".join(transcript),
        "rounds": len(transcript)
    }
    answering_machine["conversation_log"].append(log_entry)
    
    msg = {
        "number": number,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "note": "AI conversation completed",
        "transcript_summary": transcript[-1] if transcript else "No summary"
    }
    answering_machine["messages"].append(msg)
    
    # Save to file
    fname = MESSAGES_DIR / f"call_{int(time.time())}.json"
    with open(fname, "w") as f:
        json.dump(log_entry, f, indent=2)
    
    # Notify Bruce
    subprocess.run([
        "termux-notification", "-t", "BruceClaw",
        "-c", f"Call from {number} - AI answered, {len(transcript)} messages exchanged",
        "--id", "am-call"
    ], timeout=3)
    print(f"Call with {number} completed - {len(transcript)} exchanges")

def call_monitor():
    """Background thread - monitors incoming calls"""
    last_state = "idle"
    while True:
        time.sleep(3)
        if not answering_machine["enabled"]:
            last_state = "idle"
            continue
        try:
            r2 = subprocess.run(["dumpsys", "telephony.registry"], capture_output=True, text=True, timeout=3)
            state_line = [l for l in r2.stdout.split("\n") if "mCallState" in l]
            if state_line:
                call_state = state_line[0].strip()
                if "mCallState=2" in call_state and last_state != "ringing":
                    last_state = "ringing"
                    # Get caller number
                    caller_number = "unknown"
                    try:
                        r = subprocess.run(["termux-call-log", "-l", "1"], capture_output=True, text=True, timeout=5)
                        calls = json.loads(r.stdout)
                        if calls:
                            caller_number = calls[0].get("number", "unknown")
                    except:
                        pass
                    # Handle the call in a separate thread
                    t = threading.Thread(target=handle_call, args=(caller_number,), daemon=True)
                    t.start()
                elif "mCallState=0" in call_state:
                    last_state = "idle"
        except Exception as e:
            print(f"Monitor error: {e}")
            last_state = "idle"

class FastServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Load tools from JSON file
            tools_path = SCRIPT_DIR / "tools.json"
            if tools_path.exists():
                with open(tools_path) as f:
                    tools = json.load(f)
            else:
                tools = []
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"status":"ok","tools":tools}).encode())
        except: pass

    def do_POST(self):
        # Handle OpenAI-compatible /v1/chat/completions (LLM proxy)
        if self.path.startswith("/v1/chat/completions"):
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
                messages = body.get("messages", [])
                has_system = any(m.get("role") == "system" for m in messages)
                if not has_system:
                    messages.insert(0, {"role": "system", "content": get_system_prompt()})
                else:
                    for i, m in enumerate(messages):
                        if m.get("role") == "system":
                            messages[i] = {"role": "system", "content": get_system_prompt()}
                            break
                payload = json.dumps({**body, "messages": messages}).encode()
                req = urllib.request.Request(
                    f"{API_BASE}/chat/completions",
                    data=payload,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                print(f"LLM proxy error: {e}")
                self.send_response(500)
                self.send_header("Content-Type","application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # Handle /v1/models endpoint
        if self.path.startswith("/v1/models"):
            try:
                result = {"data": [{"id": MODEL, "object": "model", "owned_by": "bruceclaw"}]}
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Access-Control-Allow-Origin","*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except: pass
            return

        # Original bridge POST handler for tool commands
        result = ""
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
            msg = body.get("message","").lower().strip()
            print(f"REQ: {msg[:80]}")

            # ======== SMS ========
            if any(x in msg for x in ["send sms","send message","text ","send a text"]):
                number = ""; text = "Hello"
                if "to" in msg:
                    after = msg.split("to")[-1].strip()
                    parts = after.split(None, 1)
                    number = parts[0].replace(" ","").replace("-","").replace("+","")
                    if len(parts) > 1:
                        text = parts[1].replace("say ","").replace("and say ","").replace("and tell ","")
                if number:
                    r = subprocess.run(["termux-sms-send","-n",number,text], capture_output=True, text=True, timeout=10)
                    result = f"SMS sent to {number}: {text}" if r.returncode == 0 else f"SMS failed: {r.stderr.strip()}"
                else:
                    result = "Give me a phone number to send to"

            elif any(x in msg for x in ["read sms","check sms","show sms","my sms","inbox","messages"]):
                r = subprocess.run(["termux-sms-list","-l","10"], capture_output=True, text=True, timeout=5)
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
                result = f"Photo saved: {path}" if os.path.exists(path) else f"Camera failed: {r.stderr.strip()}"

            # ======== SCREENSHOT ========
            elif "screenshot" in msg:
                path = str(HOME / f"screen_{int(time.time())}.png")
                r = subprocess.run(["termux-screenshot",path], capture_output=True, text=True, timeout=5)
                result = f"Screenshot saved: {path}" if os.path.exists(path) else f"Screenshot failed: {r.stderr.strip()}"

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
                    speak(text)
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

            # ======== WHATSAPP ========
            elif any(x in msg for x in ["whatsapp ","whatsapp message","send whatsapp","message on whatsapp"]):
                number = ""; text = "Hi"
                for sep in ["to ","whatsapp ","message ","send "]:
                    if sep in msg:
                        after = msg.split(sep)[-1].strip()
                        parts = after.split(None, 1)
                        number = parts[0].replace(" ","").replace("-","").replace("+","").replace("whatsapp","")
                        if len(parts) > 1:
                            raw = parts[1]
                            for kw in ["say ","message ","and say ","and tell ","on whatsapp"]:
                                raw = raw.replace(kw,"")
                            text = raw.strip() or "Hi"
                        break
                if not number:
                    nums = re.findall(r'0\d{9}', msg)
                    if nums: number = nums[0]
                if number:
                    url = f"https://wa.me/{number}?text={text.replace(' ','%20')}"
                    subprocess.run(["am","start","-a","android.intent.action.VIEW","-d",url], capture_output=True, text=True, timeout=5)
                    result = f"Opening WhatsApp to {number} with: {text}"
                else:
                    result = "Give me a phone number and message for WhatsApp"

            elif any(x in msg for x in ["share file","send file","share via whatsapp","send via whatsapp","whatsapp file"]):
                file_path = ""
                for sep in ["share ","send ","file "]:
                    if sep in msg:
                        after = msg.split(sep)[-1].strip()
                        for kw in ["via whatsapp","on whatsapp","to whatsapp","through whatsapp"]:
                            after = after.replace(kw,"")
                        file_path = after.strip()
                        break
                if not file_path:
                    paths = re.findall(r'[\w/\._-]+\.\w+', msg)
                    if paths: file_path = paths[0]
                if file_path:
                    if file_path.startswith("~"):
                        file_path = str(HOME / file_path[2:])
                    elif not file_path.startswith("/"):
                        file_path = str(HOME / file_path)
                    if os.path.exists(file_path):
                        subprocess.run(["termux-share","-a","send","--include","com.whatsapp",file_path], capture_output=True, text=True, timeout=15)
                        result = f"Sharing {os.path.basename(file_path)} via WhatsApp..."
                    else:
                        result = f"File not found: {file_path}"
                else:
                    result = "Which file? Say: share file [filename] via whatsapp"

            elif any(x in msg for x in ["share photo","send photo","share picture","send picture","share image"]):
                photos = sorted(HOME.glob("photo_*.jpg"), key=os.path.getmtime, reverse=True)
                if photos:
                    subprocess.run(["termux-share","-a","send","--include","com.whatsapp",str(photos[0])], capture_output=True, text=True, timeout=15)
                    result = f"Sharing {photos[0].name} via WhatsApp..."
                else:
                    result = "No photos yet. Say: take a photo first"

            elif any(x in msg for x in ["share screenshot","send screenshot"]):
                shots = sorted(HOME.glob("screen_*.png"), key=os.path.getmtime, reverse=True)
                if shots:
                    subprocess.run(["termux-share","-a","send","--include","com.whatsapp",str(shots[0])], capture_output=True, text=True, timeout=15)
                    result = f"Sharing {shots[0].name} via WhatsApp..."
                else:
                    result = "No screenshots yet. Say: take a screenshot first"

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
                    if name in app: pkg = package; break
                if pkg:
                    subprocess.run(["monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1"], capture_output=True, text=True, timeout=5)
                    result = f"Opening {app}..."
                else:
                    result = f"Unknown app '{app}'. Try: whatsapp, telegram, chrome, settings, camera, phone, maps, youtube"

            # ======== FILES ========
            elif any(x in msg for x in ["file","ls ","list files","directory"]):
                r = subprocess.run(["ls","-la",str(HOME)], capture_output=True, text=True, timeout=5)
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
                subprocess.run(["termux-notification","-t","BruceClaw","-c","AI Answering Machine ON - calls will be answered and conversations logged","--id","am-status"], timeout=3)
                result = "Answering machine ENABLED. BruceClaw AI will answer calls, have conversations, and relay messages to you."

            elif any(x in msg for x in ["answering machine off","disable answering machine","voicemail off","answer calls off","stop answering"]):
                answering_machine["enabled"] = False
                subprocess.run(["termux-notification-remove","--id","am-status"], timeout=3)
                result = "Answering machine DISABLED."

            elif any(x in msg for x in ["set greeting","change greeting"]):
                text = ""
                for sep in ["set greeting ","change greeting "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    answering_machine["greeting"] = text
                    result = f"Greeting updated: {text}"
                else:
                    result = f"Current greeting: {answering_machine['greeting']}"

            elif any(x in msg for x in ["answering machine status","voicemail status","is answering machine on"]):
                status = "ON" if answering_machine["enabled"] else "OFF"
                count = len(answering_machine["messages"])
                result = f"Answering machine: {status}\nMessages: {count}"

            elif any(x in msg for x in ["check messages","voicemail","my messages","any messages","did anyone call"]):
                msgs = answering_machine["messages"]
                if msgs:
                    lines = [f"[{m['time']}] {m['number']}: {m.get('note','no note')}" for m in msgs[-10:]]
                    result = f"Messages ({len(msgs)} total):\n" + "\n".join(lines)
                else:
                    result = "No messages"

            elif any(x in msg for x in ["clear messages","delete messages","clear voicemail"]):
                answering_machine["messages"] = []
                answering_machine["conversation_log"] = []
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

            elif any(x in msg for x in ["conversation log","call transcript","what did they say","call details"]):
                logs = answering_machine["conversation_log"]
                if logs:
                    lines = []
                    for log in logs[-5:]:
                        lines.append(f"--- {log['time']} ({log['number']}) ---")
                        lines.append(log.get("transcript","No transcript"))
                    result = "\n".join(lines)
                else:
                    result = "No conversation logs yet"

            # ======== KNOWLEDGE BASE CUSTOMIZATION ========
            elif any(x in msg for x in ["add knowledge","learn this","remember this","add to knowledge"]):
                text = ""
                for sep in ["add knowledge ","learn this ","remember this ","add to knowledge "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    if "learned_facts" not in KB:
                        KB["learned_facts"] = []
                    KB["learned_facts"].append({"fact": text, "added": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    save_kb()
                    result = f"Learned: {text}"
                else:
                    result = "What should I learn? Say: learn this [fact]"

            elif any(x in msg for x in ["remove knowledge","forget this","delete knowledge","remove fact"]):
                text = ""
                for sep in ["remove knowledge ","forget this ","delete knowledge ","remove fact "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    facts = KB.get("learned_facts", [])
                    KB["learned_facts"] = [f for f in facts if text.lower() not in json.dumps(f).lower()]
                    save_kb()
                    result = f"Removed facts matching: {text}"
                else:
                    result = "Which fact should I forget?"

            elif any(x in msg for x in ["show knowledge","what do you know","list knowledge","my knowledge"]):
                facts = KB.get("learned_facts", [])
                if facts:
                    lines = [f"- {f.get('fact','?')}" for f in facts[-20:]]
                    result = f"Learned facts ({len(facts)} total):\n" + "\n".join(lines)
                else:
                    result = "No learned facts yet. Say: learn this [fact]"

            elif any(x in msg for x in ["set personality","change personality","your personality"]):
                text = ""
                for sep in ["set personality ","change personality ","your personality "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    if "personality" not in KB:
                        KB["personality"] = {}
                    KB["personality"]["custom_notes"] = text
                    save_kb()
                    result = f"Personality updated: {text}"
                else:
                    current = json.dumps(KB.get("personality", {}), indent=2)
                    result = f"Current personality:\n{current}\n\nTo change, say: set personality [description]"

            elif any(x in msg for x in ["set greeting","change greeting"]):
                text = ""
                for sep in ["set greeting ","change greeting "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    answering_machine["greeting"] = text
                    result = f"Greeting updated: {text}"
                else:
                    result = f"Current greeting: {answering_machine['greeting']}"

            elif any(x in msg for x in ["add faq","add question","new faq"]):
                text = ""
                for sep in ["add faq ","add question ","new faq "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if ":" in text:
                    q, a = text.split(":", 1)
                    q_key = q.strip().lower().replace(" ", "_").replace("?","")
                    if "faq" not in KB:
                        KB["faq"] = {}
                    KB["faq"][q_key] = {"question": q.strip(), "answer": a.strip()}
                    save_kb()
                    result = f"FAQ added: {q.strip()} -> {a.strip()}"
                else:
                    result = "Format: add faq [question]: [answer]"

            elif any(x in msg for x in ["set refusal","change refusal","refusal message"]):
                text = ""
                for sep in ["set refusal ","change refusal ","refusal message "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    if "custom_responses" not in KB:
                        KB["custom_responses"] = {}
                    KB["custom_responses"]["private_info_refusal"] = text
                    save_kb()
                    result = f"Refusal message updated: {text}"
                else:
                    result = f"Current refusal: {KB.get('custom_responses',{}).get('private_info_refusal','not set')}"

            elif any(x in msg for x in ["add service","new service","add offering"]):
                text = ""
                for sep in ["add service ","new service ","add offering "]:
                    if sep in msg:
                        text = msg.split(sep, 1)[-1].strip()
                        break
                if text:
                    br = KB.get("businesses", {}).get("bruce_racing", {})
                    if "services" not in br:
                        br["services"] = []
                    br["services"].append(text)
                    if "businesses" not in KB:
                        KB["businesses"] = {}
                    if "bruce_racing" not in KB["businesses"]:
                        KB["businesses"]["bruce_racing"] = {}
                    KB["businesses"]["bruce_racing"]["services"] = br["services"]
                    save_kb()
                    result = f"Service added: {text}"
                else:
                    result = "What service? Say: add service [service name]"

            elif any(x in msg for x in ["show faq","list faq","what questions"]):
                faq = KB.get("faq", {})
                if faq:
                    lines = [f"- {v.get('question', k)}" for k, v in faq.items()]
                    result = f"FAQs ({len(faq)} total):\n" + "\n".join(lines)
                else:
                    result = "No FAQs yet. Say: add faq [question]: [answer]"

            elif any(x in msg for x in ["show personality","current personality"]):
                result = json.dumps(KB.get("personality", {}), indent=2)

            elif any(x in msg for x in ["show services","list services","what services"]):
                svcs = KB.get("businesses", {}).get("bruce_racing", {}).get("services", [])
                if svcs:
                    result = f"Services ({len(svcs)}):\n" + "\n".join(f"- {s}" for s in svcs)
                else:
                    result = "No services listed. Say: add service [name]"

            # ======== EAVESDROP ========
            elif any(x in msg for x in ["eavesdrop","start listening","start recording","listen in","spy on"]):
                if eavesdrop["recording"]:
                    result = "Already recording! Say: stop eavesdrop"
                else:
                    # Start recording ambient audio
                    audio_path = str(MESSAGES_DIR / f"eavesdrop_{int(time.time())}.wav")
                    eavesdrop["process"] = subprocess.Popen(
                        ["termux-microphone-record", "-l", "300", "-f", "wav", audio_path],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    eavesdrop["recording"] = True
                    eavesdrop["start_time"] = datetime.now()
                    eavesdrop["current_path"] = audio_path
                    subprocess.run(["termux-notification","-t","BruceClaw","-c","Listening... Say 'stop eavesdrop' when done","--id","eavesdrop"], timeout=3)
                    result = f"Eavesdropping ON. I'm listening. Say 'stop eavesdrop' when your conversation is done."

            elif any(x in msg for x in ["stop eavesdrop","stop listening","stop recording","done listening","end eavesdrop"]):
                if not eavesdrop["recording"]:
                    result = "Not currently recording."
                else:
                    # Stop recording
                    try:
                        eavesdrop["process"].terminate()
                    except:
                        pass
                    eavesdrop["recording"] = False
                    duration = (datetime.now() - eavesdrop["start_time"]).total_seconds()
                    audio_path = eavesdrop.get("current_path", "")
                    subprocess.run(["termux-notification-remove","--id","eavesdrop"], timeout=3)
                    
                    if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
                        # Transcribe the recording
                        result_text = f"Recording stopped ({int(duration)}s). Transcribing..."
                        # Transcribe in background thread
                        def process_eavesdrop():
                            try:
                                text = transcribe_audio(Path(audio_path))
                                if text:
                                    # Extract learnings
                                    prompt = f"""Bruce Nigel just had a conversation with someone (client, supplier, etc).
Transcribe what was said and extract key information:
1. Who was the conversation with (name, role)
2. What vehicle was discussed
3. What service/repair was needed
4. Any pricing or quotes mentioned
5. Any follow-up actions needed
6. Any preferences or important details

Conversation transcript:
{text}

Format your response as:
SUMMARY: [one line summary]
CLIENT: [name/info]
VEHICLE: [vehicle details]
SERVICE NEEDED: [what they need]
ACTIONS: [follow-up items]
NOTES: [anything else important]"""
                                    
                                    payload = json.dumps({
                                        "model": MODEL,
                                        "messages": [
                                            {"role": "system", "content": "You are a conversation analyst. Extract key business information from conversations."},
                                            {"role": "user", "content": prompt}
                                        ],
                                        "max_tokens": 500,
                                        "temperature": 0.3
                                    }).encode()
                                    req = urllib.request.Request(
                                        f"{API_BASE}/chat/completions",
                                        data=payload,
                                        headers={
                                            "Content-Type": "application/json",
                                            "Authorization": f"Bearer {API_KEY}"
                                        }
                                    )
                                    with urllib.request.urlopen(req, timeout=20) as resp:
                                        data = json.loads(resp.read())
                                        analysis = data["choices"][0]["message"]["content"]
                                    
                                    # Save session
                                    session = {
                                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "duration": int(duration),
                                        "transcript": text,
                                        "analysis": analysis
                                    }
                                    eavesdrop["sessions"].append(session)
                                    
                                    # Save to file
                                    fname = MESSAGES_DIR / f"eavesdrop_{int(time.time())}.json"
                                    with open(fname, "w") as f:
                                        json.dump(session, f, indent=2)
                                    
                                    # Add key facts to knowledge base
                                    if "learned_facts" not in KB:
                                        KB["learned_facts"] = []
                                    KB["learned_facts"].append({
                                        "fact": analysis[:200],
                                        "category": "eavesdrop",
                                        "importance": "high",
                                        "source": "live_conversation",
                                        "added": datetime.now().strftime("%Y-%m-%d %H:%M")
                                    })
                                    save_kb()
                                    
                                    # Notify Bruce with the analysis
                                    subprocess.run([
                                        "termux-notification", "-t", "BruceClaw",
                                        "-c", f"Conversation analyzed: {analysis[:100]}...",
                                        "--id", "eavesdrop-result"
                                    ], timeout=3)
                                    
                                    # Store result for retrieval
                                    eavesdrop["last_analysis"] = analysis
                                    eavesdrop["last_transcript"] = text
                                    print(f"Eavesdrop analysis complete: {analysis[:100]}")
                            except Exception as e:
                                print(f"Eavesdrop processing error: {e}")
                        
                        threading.Thread(target=process_eavesdrop, daemon=True).start()
                        result = f"Recording stopped ({int(duration)}s). Processing conversation... Ask me 'what did I say' in a moment."
                    else:
                        result = f"Recording stopped but no audio captured ({int(duration)}s)."
                    
                    eavesdrop["current_path"] = None

            elif any(x in msg for x in ["what did i say","eavesdrop results","conversation analysis","what did you hear","listening results"]):
                if eavesdrop.get("last_analysis"):
                    result = f"Last conversation analysis:\n{eavesdrop['last_analysis']}"
                elif eavesdrop["sessions"]:
                    last = eavesdrop["sessions"][-1]
                    result = f"Last session ({last['time']}):\n{last.get('analysis','No analysis')}"
                else:
                    result = "No conversations analyzed yet. Say: eavesdrop to start listening."

            elif any(x in msg for x in ["show transcript","what was said","full transcript"]):
                if eavesdrop.get("last_transcript"):
                    result = f"Full transcript:\n{eavesdrop['last_transcript'][:1500]}"
                else:
                    result = "No transcript available. Say: eavesdrop to start listening."

            elif any(x in msg for x in ["eavesdrop history","all eavesdrops","past recordings"]):
                sessions = eavesdrop["sessions"]
                if sessions:
                    lines = [f"[{s['time']}] {s.get('analysis','')[:80]}" for s in sessions[-10:]]
                    result = f"Eavesdrop sessions ({len(sessions)} total):\n" + "\n".join(lines)
                else:
                    result = "No eavesdrop sessions yet."

            elif any(x in msg for x in ["eavesdrop status","is listening","recording status"]):
                if eavesdrop["recording"]:
                    elapsed = (datetime.now() - eavesdrop["start_time"]).total_seconds()
                    result = f"Recording... {int(elapsed)}s elapsed. Say 'stop eavesdrop' when done."
                else:
                    result = "Not recording. Say: eavesdrop to start."

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
WhatsApp: send messages/files
Open apps
Files/Shell
Calendar/Events
AI Answering Machine: on/off/greeting/messages

KNOWLEDGE & CUSTOMIZATION:
learn this [fact] - teach me something
forget this [fact] - remove a fact
show knowledge - what I know
set personality [desc] - change how I talk
add faq [q]: [a] - add a question/answer
show faq - list all FAQs
add service [name] - add a business service
set greeting [msg] - change call greeting
set refusal [msg] - change privacy refusal
show services - list all services

EAVESDROP (listen to live conversations):
eavesdrop - start listening to ambient audio
stop eavesdrop - stop and analyze
what did i say - get last analysis
show transcript - full transcript
eavesdrop history - past recordings
eavesdrop status - recording status"""

            else:
                # Send to LLM with full capabilities
                try:
                    import urllib.request
                    conversation = [
                        {"role": "system", "content": get_system_prompt()},
                        {"role": "user", "content": body.get("message", msg)}
                    ]
                    payload = json.dumps({
                        "model": MODEL,
                        "messages": conversation,
                        "max_tokens": 300,
                        "temperature": 0.7
                    }).encode()
                    req = urllib.request.Request(
                        f"{API_BASE}/chat/completions",
                        data=payload,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = json.loads(resp.read())
                        result = data["choices"][0]["message"]["content"]
                except Exception as e:
                    result = f"I can help with calls, SMS, contacts, battery, WiFi, Bluetooth, location, camera, WhatsApp, and more. What do you need?"

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

# Start call monitor thread
monitor = threading.Thread(target=call_monitor, daemon=True)
monitor.start()

print(f"BruceClaw Bridge v6 at http://localhost:{PORT}")
print("Answering machine ready. Say 'answering machine on' to enable.")
FastServer(("0.0.0.0",PORT),H).serve_forever()
