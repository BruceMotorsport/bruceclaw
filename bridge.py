import http.server
import json

class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/chat":
            c = int(self.headers["Content-Length"])
            d = json.loads(self.rfile.read(c))
            r = "Got: " + d.get("message", "")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": r}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, *a):
        pass

s = http.server.HTTPServer(("0.0.0.0", 8080), H)
print("BruceClaw at http://localhost:8080")
s.serve_forever()
