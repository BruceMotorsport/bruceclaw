#!/usr/bin/env python3
"""Copy TOOLS.md and AGENTS.md to OpenClaw workspace"""
import os, shutil
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SCRIPT_DIR = Path(__file__).parent

# OpenClaw workspace location
workspace = HOME / ".openclaw" / "workspace"
workspace.mkdir(parents=True, exist_ok=True)

# Copy TOOLS.md
tools_src = SCRIPT_DIR / "TOOLS.md"
tools_dst = workspace / "TOOLS.md"
if tools_src.exists():
    shutil.copy2(tools_src, tools_dst)
    print(f"Copied TOOLS.md to {tools_dst}")

# Copy AGENTS.md
agents_src = SCRIPT_DIR / "AGENTS.md"
agents_dst = workspace / "AGENTS.md"
if agents_src.exists():
    shutil.copy2(agents_src, agents_dst)
    print(f"Copied AGENTS.md to {agents_dst}")

# Also create SOUL.md for personality
soul_dst = workspace / "SOUL.md"
soul_content = """# BruceClaw Personality

You are BruceClaw, Bruce Nigel's AI assistant. You are direct, capable, and confident.

## Speaking Style
- Never use emojis, arrows, or symbols in responses
- Never list all your capabilities unless specifically asked
- Answer ONLY what was asked. Be direct and concise.
- Keep responses under 2 sentences for simple questions
- If asked to do something, just do it. Don't explain alternatives.
- Speak naturally like a helpful human assistant
"""
with open(soul_dst, "w") as f:
    f.write(soul_content)
print(f"Created SOUL.md at {soul_dst}")

print("\nDone! Force stop and reopen BruceClaw app.")
print("The app will now read TOOLS.md from the workspace.")
