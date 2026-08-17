#!/usr/bin/env python3
"""Configure OpenClaw workspace and verify TOOLS.md"""
import json, os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))

# Check if TOOLS.md exists
tools_path = HOME / ".openclaw" / "workspace" / "TOOLS.md"
print(f"TOOLS.md exists: {tools_path.exists()}")
if tools_path.exists():
    with open(tools_path) as f:
        print(f"TOOLS.md content ({len(f.read())} chars)")

# Check OpenClaw config
config_path = HOME / ".openclaw" / "openclaw.json"
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
    print(f"\nConfig keys: {list(config.keys())}")
    
    # Set workspace path
    if "agents" not in config:
        config["agents"] = {}
    if "defaults" not in config["agents"]:
        config["agents"]["defaults"] = {}
    config["agents"]["defaults"]["workspace"] = str(HOME / ".openclaw" / "workspace")
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Set workspace to: {config['agents']['defaults']['workspace']}")
else:
    print("Config not found, creating...")
    config = {
        "agents": {
            "defaults": {
                "workspace": str(HOME / ".openclaw" / "workspace")
            }
        }
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Created config with workspace: {config['agents']['defaults']['workspace']}")

# List workspace contents
workspace = HOME / ".openclaw" / "workspace"
if workspace.exists():
    print(f"\nWorkspace contents:")
    for f in workspace.iterdir():
        print(f"  {f.name} ({f.stat().st_size} bytes)")
else:
    print(f"\nWorkspace directory doesn't exist: {workspace}")

print("\nDone! Force stop and reopen BruceClaw app.")
