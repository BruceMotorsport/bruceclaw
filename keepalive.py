#!/usr/bin/env python3
"""Keeps Termux alive by running a lightweight server"""
import http.server, json, time, os

PORT = 9999

class KeepAliveHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status":"alive",
            "uptime": time.time(),
            "pid": os.getpid()
        }).encode())
    def log_message(self,*a): pass

print(f"KeepAlive running on port {PORT}")
http.server.HTTPServer(("0.0.0.0",PORT), KeepAliveHandler).serve_forever()
