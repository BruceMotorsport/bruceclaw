import http.server
import json
import os

HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BruceClaw</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f0f13;color:#fff;height:100vh;display:flex;flex-direction:column}
.h{background:#16213e;padding:20px;text-align:center;border-bottom:2px solid #f97316}
.h h1{color:#f97316;font-size:28px}
.h .s{color:#22c55e;font-size:14px;margin-top:4px}
.c{flex:1;overflow-y:auto;padding:20px}
.m{margin-bottom:14px;padding:14px 18px;border-radius:16px;max-width:85%;font-size:18px;line-height:1.6}
.u{background:#f97316;color:#fff;margin-left:auto;border-bottom-right-radius:4px}
.b{background:#1c1c27;color:#e0e0e0;border-bottom-left-radius:4px}
.i{display:flex;padding:12px;background:#16213e;gap:10px}
.i input{flex:1;background:#1c1c27;border:1px solid #333;color:#fff;padding:14px;border-radius:10px;font-size:18px}
.i button{background:#f97316;color:#fff;border:none;padding:14px 24px;border-radius:10px;font-size:18px;font-weight:bold}
</style>
</head>
<body>
<div class="h"><h1>BruceClaw</h1><div class="s">Connected</div></div>
<div class="c" id="c"><div class="m b">Hey! I'm BruceClaw. Ask me anything.</div></div>
<div class="i"><input type="text" id="i" placeholder="Type a message..." autofocus><button onclick="send()">Send</button></div>
<script>
var c=document.getElementById("c"),i=document.getElementById("i");
function a(t,u){var d=document.createElement("div");d.className="m "+(u?"u":"b");d.textContent=t;c.appendChild(d);c.scrollTop=c.scrollHeight}
function send(){var m=i.value.trim();if(!m)return;a(m,1);i.value="";a("Thinking...",0);fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})}).then(function(r){return r.json()}).then(function(d){c.removeChild(c.lastChild);a(d.reply||d.error||"No response",0)}).catch(function(e){c.removeChild(c.lastChild);a("Error: "+e.message,0)})}
i.addEventListener("keypress",function(e){if(e.key==="Enter")send()});
</script>
</body>
</html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

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
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, *a):
        pass

s = http.server.HTTPServer(("0.0.0.0", 8090), H)
print("BruceClaw at http://localhost:8090")
s.serve_forever()
