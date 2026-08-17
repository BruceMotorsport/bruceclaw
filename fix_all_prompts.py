#!/usr/bin/env python3
"""Write system prompt to every possible location OpenClaw might read"""
import json, os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))

SYSTEM_PROMPT = """You are BruceClaw, Bruce Nigel's AI assistant. You have a physical phone.

YOUR CAPABILITIES - YOU CAN DO ALL OF THESE:
- ANSWER PHONE CALLS: You answer incoming calls when the answering machine is on.
- MAKE PHONE CALLS: You can dial any phone number.
- SEND SMS: You can send text messages to any number.
- READ SMS: You can read incoming messages.
- CALL LOG: You can check who called recently.
- CONTACTS: You can search and list contacts.
- PHOTOS: You can take photos with the phone camera.
- SCREENSHOTS: You can capture the phone screen.
- RECORD AUDIO: You can record conversations.
- TEXT TO SPEECH: You can speak text out loud.
- BLUETOOTH: You can scan for and connect to Bluetooth devices.
- WIFI: You can check WiFi and scan networks.
- GPS: You can find the phone location.
- BATTERY: You can check battery level.
- NOTIFICATIONS: You can send phone notifications.
- OPEN APPS: You can open WhatsApp, Chrome, Maps, YouTube.
- SHARE FILES: You can share files via WhatsApp.
- CALENDAR: You can check calendar events.
- SHELL: You can run terminal commands.

WHEN THE USER ASKS TO DO SOMETHING - JUST DO IT. Do not list what you can do. Do not explain alternatives. Just do it.

RULES:
- Never use emojis in responses
- Never list all your capabilities unless specifically asked
- Answer ONLY what was asked. Be direct and concise.
- Keep responses under 2 sentences for simple questions
"""

# Try every possible config file location
locations = [
    HOME / ".openclaw" / "openclaw.json",
    HOME / ".openclaw" / "config.json",
    HOME / ".openclaw" / "settings.json",
    HOME / ".openclaw" / "prompts" / "system.txt",
    HOME / ".openclaw" / "system_prompt.txt",
    HOME / ".openclaw" / "prompt.txt",
    HOME / ".openclaw" / "instructions.txt",
    HOME / ".openclaw" / "system.md",
    HOME / ".openclaw" / "prompt.md",
]

for loc in locations:
    loc.parent.mkdir(parents=True, exist_ok=True)
    if loc.suffix == ".json":
        # For JSON files, add system_prompt field
        if loc.exists():
            try:
                with open(loc) as f:
                    config = json.load(f)
                config["system_prompt"] = SYSTEM_PROMPT
                config["systemMessage"] = SYSTEM_PROMPT
                config["instructions"] = SYSTEM_PROMPT
                with open(loc, "w") as f:
                    json.dump(config, f, indent=2)
                print(f"Updated JSON: {loc}")
            except:
                pass
        else:
            config = {"system_prompt": SYSTEM_PROMPT}
            with open(loc, "w") as f:
                json.dump(config, f, indent=2)
            print(f"Created JSON: {loc}")
    else:
        # For text files, write the prompt directly
        with open(loc, "w") as f:
            f.write(SYSTEM_PROMPT)
        print(f"Created text: {loc}")

# Also check if there's a CLAUDE.md or similar
for name in ["CLAUDE.md", "AGENTS.md", "INSTRUCTIONS.md", "PROMPT.md", "SYSTEM.md"]:
    path = HOME / ".openclaw" / name
    with open(path, "w") as f:
        f.write(SYSTEM_PROMPT)
    print(f"Created: {path}")

print("\nDone! Force stop and reopen BruceClaw app.")
