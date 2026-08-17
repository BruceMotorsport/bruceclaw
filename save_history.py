#!/usr/bin/env python3
"""Save conversation history to disk"""
import json, os
from pathlib import Path
from datetime import datetime

HOME = Path(os.path.expanduser("~"))
HISTORY_FILE = HOME / "Desktop" / "Simone-Lazarus" / "logs" / "conversation_history.json"

def save_conversation(messages):
    """Save conversation to disk"""
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    
    history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": messages
    })
    
    # Keep last 50 conversations
    history = history[-50:]
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    
    print(f"Saved {len(messages)} messages")

def load_conversation():
    """Load last conversation from disk"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            history = json.load(f)
        if history:
            return history[-1]["messages"]
    return []

if __name__ == "__main__":
    # Test
    messages = load_conversation()
    print(f"Loaded {len(messages)} messages from last conversation")
