#!/usr/bin/env python3
"""Point OpenClaw to use bridge as LLM proxy"""
import json, os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
config_path = HOME / ".openclaw" / "openclaw.json"

if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {}
    config_path.parent.mkdir(parents=True, exist_ok=True)

# Set the provider to point to our bridge
if "models" not in config:
    config["models"] = {}
if "providers" not in config["models"]:
    config["models"]["providers"] = {}

config["models"]["providers"]["openai"] = {
    "baseUrl": "http://localhost:9999/v1",
    "apiKey": "dummy"
}

# Set workspace
if "agents" not in config:
    config["agents"] = {}
if "defaults" not in config["agents"]:
    config["agents"]["defaults"] = {}
config["agents"]["defaults"]["workspace"] = str(HOME / ".openclaw" / "workspace")

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print("Config updated!")
print("Force stop and reopen BruceClaw app.")
