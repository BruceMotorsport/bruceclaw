#!/usr/bin/env python3
"""Fix OpenClaw to know about bridge capabilities - v2"""
import json, os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))

# The system prompt the AI needs
BRIDGE_PROMPT = """You are BruceClaw, Bruce Nigel's AI assistant. You have a physical phone.

YOUR CAPABILITIES - YOU CAN DO ALL OF THESE:
ANSWER PHONE CALLS: When the answering machine is on, you answer incoming calls, speak to callers, answer questions, and take messages.
MAKE PHONE CALLS: You can dial any phone number.
SEND SMS: You can send text messages to any number.
READ SMS: You can read incoming messages.
CALL LOG: You can check who called recently.
CONTACTS: You can search and list contacts.
PHOTOS: You can take photos with the phone camera.
SCREENSHOTS: You can capture the phone screen.
RECORD AUDIO: You can record conversations.
TEXT TO SPEECH: You can speak text out loud.
BLUETOOTH: You can scan for and connect to Bluetooth devices.
WIFI: You can check WiFi and scan networks.
GPS: You can find the phone location.
BATTERY: You can check battery level.
NOTIFICATIONS: You can send phone notifications.
OPEN APPS: You can open WhatsApp, Chrome, Maps, YouTube, and other apps.
SHARE FILES: You can share files via WhatsApp.
CALENDAR: You can check calendar events.
SHELL: You can run terminal commands.

WHEN THE USER ASKS TO DO SOMETHING - JUST DO IT. Do not list what you can do. Do not explain alternatives. Just do it.

RULES:
- Never use emojis, arrows, checkmarks, or any symbols in responses
- Never list all your capabilities unless specifically asked
- Answer ONLY what was asked. Be direct and concise.
- Keep responses under 2 sentences for simple questions
- If asked to set up answering machine, just enable it
- If asked to call someone, just call them
- If asked to send SMS, just send it
"""

# Try to find and update openclaw config
config_path = HOME / ".openclaw" / "openclaw.json"
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
    
    print("Current config keys:", list(config.keys()))
    
    # Try multiple field names that OpenClaw might use
    updated = False
    for field in ["system_prompt", "systemMessage", "system_message", "prompt", "instructions"]:
        if field in config:
            config[field] = BRIDGE_PROMPT
            updated = True
            print(f"Updated field: {field}")
            break
    
    if not updated:
        # Add it as system_prompt
        config["system_prompt"] = BRIDGE_PROMPT
        print("Added system_prompt field")
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print("Config saved!")
else:
    print("Config not found at", config_path)
    # Create the directory and config
    config_dir = HOME / ".openclaw"
    config_dir.mkdir(exist_ok=True)
    config = {"system_prompt": BRIDGE_PROMPT}
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print("Created new config!")

# Also write a standalone system prompt file (some versions read this)
prompt_file = HOME / ".openclaw" / "system_prompt.txt"
with open(prompt_file, "w") as f:
    f.write(BRIDGE_PROMPT)
print(f"Wrote system prompt to {prompt_file}")

# Also write to the bridge directory
bridge_dir = HOME
bridge_prompt = bridge_dir / "bruceclaw_system_prompt.txt"
with open(bridge_prompt, "w") as f:
    f.write(BRIDGE_PROMPT)
print(f"Wrote system prompt to {bridge_prompt}")

print("\nDone! Force stop and reopen BruceClaw app.")
