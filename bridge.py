#!/usr/bin/env python3
"""
BruceClaw Bridge v2 — Full toolbox
Exposes: tools, MCP servers, skills, files, shell, memory
"""
import http.server, json, subprocess, os, glob, time
from pathlib import Path

PORT = 8080
HOME = Path(os.path.expanduser("~"))
LAZARUS = HOME / "Lazarus"

class Toolbox:
    """All available tools"""
    
    TOOLS = {
        "files": "List, read, write, copy, move, delete files",
        "shell": "Run shell commands",
        "sms": "Read and send SMS",
        "contacts": "Read phone contacts",
        "calendar": "Read calendar events",
        "camera": "Take photos",
        "web": "Browse the internet",
        "memory": "Read/write Lazarus memory",
        "skills": "List and use installed skills",
        "mcp": "Connect to MCP servers",
        "notify": "Send notifications",
        "tts": "Text to speech",
        "battery": "Check battery status",
        "wifi": "Check WiFi status",
        "storage": "Check storage space",
        "install": "Install packages via pkg",
    }
    
    @staticmethod
    def list_files(path=None):
        p = Path(path) if path else HOME
        files = []
        for f in sorted(p.iterdir()):
            if not f.name.startswith("."):
                files.append({"name": f.name, "is_dir": f.is_dir(), "size": f.stat().st_size if f.is_file() else 0})
        return files[:50]
    
    @staticmethod
    def read_file(path):
        with open(path) as f:
            return f.read()[:50000]
    
    @staticmethod
    def run_command(cmd):
        # Safety check
        blocked = ["rm -rf /", "sudo", "chmod 777", "mkfs", "dd if="]
        for b in blocked:
            if b in cmd:
                return f"BLOCKED: Dangerous command '{b}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout or result.stderr or "Done"
    
    @staticmethod
    def list_skills():
        skills_dir = LAZARUS / "skills"
        if not skills_dir.exists():
            return []
        return [f.name for f in skills_dir.iterdir() if f.is_dir()]
    
    @staticmethod
    def list_mcp():
        mcp_dir = LAZARUS / "mcp"
        if not mcp_dir.exists():
            return []
        servers = []
        for f in mcp_dir.glob("*.json"):
            with open(f) as fh:
                data = json.load(fh)
                servers.append({"name": f.stem, "config": data})
        return servers
    
    @staticmethod
    def get_memory():
        mem_file = LAZARUS / "memory" / "memories.json"
        if mem_file.exists():
            with open(mem_file) as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_memory(category, key, value):
        mem_file = LAZARUS / "memory" / "memories.json"
        mem_file.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if mem_file.exists():
            with open(mem_file) as f:
                data = json.load(f)
        if category not in data:
            data[category] = {}
        data[category][key] = {"value": value, "timestamp": time.time()}
        with open(mem_file, "w") as f:
            json.dump(data, f, indent=2)
        return True

import threading

class H(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data):
        try:
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            pass
    def do_GET(self):
        if self.path == "/":
            # Return toolbox status
            tools = list(Toolbox.TOOLS.keys())
            skills = Toolbox.list_skills()
            mcp = Toolbox.list_mcp()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "agent": "BruceClaw",
                "tools": tools,
                "skills": skills,
                "mcp": [s["name"] for s in mcp],
                "lazarus": str(LAZARUS)
            }).encode())
        elif self.path.startswith("/tools"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(Toolbox.TOOLS).encode())
        elif self.path.startswith("/memory"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(Toolbox.get_memory()).encode())
        elif self.path.startswith("/skills"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(Toolbox.list_skills()).encode())
        elif self.path.startswith("/mcp"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(Toolbox.list_mcp()).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            # Handle both formats: action-based and message-based
            message = body.get("message", body.get("messages", [{}])[-1].get("content", ""))
            action = body.get("action", "")
            if not action and message:
                msg = message.lower()
                if "tool" in msg or "skill" in msg or "capabilit" in msg or "mcp" in msg or "memory" in msg or "list" in msg:
                    action = "list_tools"
            params = body.get("params", {})
            
            result = ""
            if action == "list_files":
                result = json.dumps(Toolbox.list_files(params.get("path")))
            elif action == "read_file":
                result = Toolbox.read_file(params.get("path", ""))
            elif action == "run":
                result = Toolbox.run_command(params.get("command", ""))
            elif action == "save_memory":
                Toolbox.save_memory(params.get("category", "general"), params.get("key", ""), params.get("value", ""))
                result = "Memory saved"
            elif action == "get_memory":
                result = json.dumps(Toolbox.get_memory())
            elif action == "list_tools":
                result = json.dumps(Toolbox.TOOLS)
            else:
                result = f"Unknown action: {action}"
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": result, "choices": [{"message": {"content": result}}]}).encode())
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": f"Error: {e}"}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, *a):
        pass

print(f"BruceClaw Bridge v2 at http://localhost:{PORT}")
print(f"Lazarus: {LAZARUS}")
print(f"Tools: {list(Toolbox.TOOLS.keys())}")
http.server.HTTPServer(("0.0.0.0", PORT), H).serve_forever()
