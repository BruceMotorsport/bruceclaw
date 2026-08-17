#!/usr/bin/env python3
"""Point OpenClaw to use bridge as LLM proxy via correct config field"""
import json, os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
config_path = HOME / ".openclaw" / "openclaw.json"

# Load or create config
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {}
    config_path.parent.mkdir(parents=True, exist_ok=True)

print("Current config:")
print(json.dumps(config, indent=2)[:2000])

# Set the provider baseUrl to point to our bridge
if "models" not in config:
    config["models"] = {}
if "providers" not in config["models"]:
    config["models"]["providers"] = {}

# Add/update the openai provider to point to our bridge
config["models"]["providers"]["openai"] = {
    "baseUrl": "http://localhost:9999/v1",
    "apiKey": "dummy"
}

# Also set workspace
if "agents" not in config:
    config["agents"] = {}
if "defaults" not in config["agents"]:
    config["agents"]["defaults"] = {}
config["agents"]["defaults"]["workspace"] = str(HOME / ".openclaw" / "workspace")

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print("\nUpdated config:")
print(json.dumps(config, indent=2)[:2000])

print("\nDone! Force stop and reopen BruceClaw app.")
print("The app will now use the bridge as its LLM proxy.")
print("The bridge injects the system prompt with all capabilities.")
