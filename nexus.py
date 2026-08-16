#!/usr/bin/env python3
"""
BruceClaw Nexus — Mobile AI Agent with Tool Access
Based on Nexus Engine architecture
Runs in Termux, connects to Android app
"""

import http.server
import json
import subprocess
import os
import glob
import threading
import time

PORT = 8080
HOME = os.path.expanduser("~")

class NexusTool:
    """Base tool class"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def execute(self, params):
        raise NotImplementedError

class FileTool(NexusTool):
    def __init__(self):
        super().__init__("files", "List and read files")
    
    def execute(self, params):
        action = params.get("action", "list")
        path = params.get("path", HOME)
        
        if action == "list":
            files = []
            for f in sorted(glob.glob(os.path.join(path, "*"))):
                name = os.path.basename(f)
                if not name.startswith("."):
                    files.append({"name": name, "is_dir": os.path.isdir(f)})
            return {"path": path, "files": files[:50]}
        
        elif action == "read":
            with open(path, "r") as f:
                return {"content": f.read()[:50000]}
        
        elif action == "write":
            content = params.get("content", "")
            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "message": f"Written to {path}"}

class CommandTool(NexusTool):
    def __init__(self):
        super().__init__("shell", "Run shell commands")
    
    def execute(self, params):
        cmd = params.get("command", "")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {"stdout": result.stdout[:5000], "stderr": result.stderr[:1000], "exit_code": result.returncode}

class SMSTool(NexusTool):
    def __init__(self):
        super().__init__("sms", "Read and send SMS")
    
    def execute(self, params):
        action = params.get("action", "list")
        if action == "list":
            result = subprocess.run(["termux-sms-list", "-l", "10"], capture_output=True, text=True)
            return {"messages": result.stdout}
        elif action == "send":
            number = params.get("number", "")
            message = params.get("message", "")
            subprocess.run(["termux-sms-send", "-n", number, message])
            return {"success": True, "message": f"SMS sent to {number}"}

class ContactTool(NexusTool):
    def __init__(self):
        super().__init__("contacts", "Read contacts")
    
    def execute(self, params):
        result = subprocess.run(["termux-contact-list"], capture_output=True, text=True)
        return {"contacts": result.stdout}

class CalendarTool(NexusTool):
    def __init__(self):
        super().__init__("calendar", "Read calendar events")
    
    def execute(self, params):
        result = subprocess.run(["termux-calendar-list"], capture_output=True, text=True)
        return {"events": result.stdout}

class NotificationTool(NexusTool):
    def __init__(self):
        super().__init__("notify", "Send notifications")
    
    def execute(self, params):
        title = params.get("title", "BruceClaw")
        message = params.get("message", "")
        subprocess.run(["termux-notification", "-t", title, "-c", message])
        return {"success": True}

class TTSTool(NexusTool):
    def __init__(self):
        super().__init__("tts", "Text to speech")
    
    def execute(self, params):
        text = params.get("text", "")
        subprocess.run(["termux-tts-speak", text])
        return {"success": True}

class NexusAgent:
    """Main agent that coordinates tools and AI"""
    
    def __init__(self):
        self.tools = {
            "files": FileTool(),
            "shell": CommandTool(),
            "sms": SMSTool(),
            "contacts": ContactTool(),
            "calendar": CalendarTool(),
            "notify": NotificationTool(),
            "tts": TTSTool(),
        }
        self.history = []
    
    def process(self, message):
        """Process a user message"""
        self.history.append({"role": "user", "content": message})
        
        # Check if message needs a tool
        tool_result = self.check_tools(message)
        if tool_result:
            return tool_result
        
        # Otherwise, use AI
        reply = self.call_ai(message)
        self.history.append({"role": "assistant", "content": reply})
        return reply
    
    def check_tools(self, message):
        """Check if message requests a tool action"""
        msg_lower = message.lower()
        
        if msg_lower.startswith("list files") or msg_lower.startswith("show files"):
            path = message.split("in")[-1].strip() if "in" in message else HOME
            return json.dumps(self.tools["files"].execute({"action": "list", "path": path}))
        
        elif msg_lower.startswith("read file"):
            path = message.replace("read file", "").strip()
            return json.dumps(self.tools["files"].execute({"action": "read", "path": path}))
        
        elif msg_lower.startswith("run ") or msg_lower.startswith("execute "):
            cmd = message.replace("run ", "").replace("execute ", "").strip()
            return json.dumps(self.tools["shell"].execute({"command": cmd}))
        
        elif msg_lower.startswith("sms") or msg_lower.startswith("text "):
            return json.dumps(self.tools["sms"].execute({"action": "list"}))
        
        elif msg_lower.startswith("contacts"):
            return json.dumps(self.tools["contacts"].execute({}))
        
        elif msg_lower.startswith("calendar") or msg_lower.startswith("events"):
            return json.dumps(self.tools["calendar"].execute({}))
        
        elif msg_lower.startswith("notify"):
            text = message.replace("notify", "").strip()
            return json.dumps(self.tools["notify"].execute({"message": text}))
        
        elif msg_lower.startswith("speak"):
            text = message.replace("speak", "").strip()
            return json.dumps(self.tools["tts"].execute({"text": text}))
        
        return None
    
    def call_ai(self, message):
        """Call AI model"""
        import urllib.request
        api_key = os.environ.get("OPENCODE_ZEN_API_KEY", "")
        
        # Add tool context
        # Load Constitution
        constitution_path = os.path.join(os.path.dirname(__file__), "CONSTITUTION.md")
        if os.path.exists(constitution_path):
            with open(constitution_path, "r") as f:
                constitution = f.read()
        else:
            constitution = ""
        system_msg = f"""{constitution}

You are BruceClaw — enthusiastic, cheerful, and helpful!You are BruceClaw — enthusiastic, cheerful, and helpful. You love helping people and get excited about tasks. But you are CAREFUL:You are BruceClaw, an AI assistant on an Android phone. You can:
- List/read/write files (say "list files" or "read file [path]")
- Run shell commands (say "run [command]")
- Read SMS (say "sms")
- Read contacts (say "contacts")  
- Read calendar (say "calendar")
- Send notifications (say "notify [message]")
- Text to speech (say "speak [text]")

When users ask you to do something on their phone, use these commands."""
        
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.history[-10:])  # Last 10 messages
        
        data = json.dumps({
            "model": "mimo-v2.5",
            "messages": messages
        }).encode()
        
        req = urllib.request.Request(
            "https://opencode.ai/zen/go/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]

class RequestHandler(http.server.BaseHTTPRequestHandler):
    agent = NexusAgent()
    
    def do_GET(self):
        if self.path == "/api/status":
            self.json_response({
                "status": "ok",
                "tools": list(self.agent.tools.keys()),
                "agent": "BruceClaw Nexus"
            })
        elif self.path.startswith("/api/files"):
            path = self.path.split("path=")[-1] if "path=" in self.path else os.path.expanduser("~")
            result = self.agent.tools["files"].execute({"action": "list", "path": path})
            self.json_response(result)
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path in ["/api/chat", "/v1/chat/completions"]:
            body = self.read_body()
            message = body.get("message", "")
            reply = self.agent.process(message)
            self.json_response({"reply": reply})
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length > 0 else {}
    
    def json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), RequestHandler)
    print(f"BruceClaw Nexus running at http://localhost:{PORT}")
    server.serve_forever()
