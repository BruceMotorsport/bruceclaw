#!/usr/bin/env python3
"""
BruceClaw Web UI Server
Serves chat interface and connects to OpenClaw
"""

import http.server
import json
import subprocess
import os

PORT = 8080
OPENCLAW_DIR = os.path.expanduser("~/bruceclaw/openclaw")

class BruceClawHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            message = data.get('message', '')
            
            # Send to OpenClaw
            try:
                result = subprocess.run(
                    ['node', 'openclaw.mjs', '--message', message],
                    cwd=OPENCLAW_DIR,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                reply = result.stdout.strip() or result.stderr.strip() or 'No response from OpenClaw'
            except Exception as e:
                reply = f'Error: {str(e)}'
            
            response = json.dumps({'reply': reply})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode())
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

os.chdir(os.path.dirname(os.path.abspath(__file__)))
server = http.server.HTTPServer(('0.0.0.0', PORT), BruceClawHandler)
print(f'BruceClaw running at http://localhost:{PORT}')
server.serve_forever()
