#!/usr/bin/env python3
"""Point OpenClaw to use bridge as LLM proxy"""
import json, os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
config_path = HOME / ".openclaw" / "openclaw.json"

if not config_path.exists():
    print("Config not found at", config_path)
    exit(1)

with open(config_path) as f:
    config = json.load(f)

print("Current config:")
print(json.dumps(config, indent=2)[:2000])

# Change the API base URL to point to our bridge
# The bridge runs on localhost:9999 and has /v1/chat/completions endpoint
if "providers" in config:
    for name, provider in config["providers"].items():
        if "base_url" in provider or "apiBase" in provider or "url" in provider:
            old_url = provider.get("base_url", provider.get("apiBase", provider.get("url", "")))
            print(f"\nProvider '{name}' current URL: {old_url}")
            # Point to our bridge
            provider["base_url"] = "http://localhost:9999/v1"
            print(f"Changed to: http://localhost:9999/v1")
        elif "apiBase" in provider:
            print(f"\nProvider '{name}' current apiBase: {provider['apiBase']}")
            provider["apiBase"] = "http://localhost:9999/v1"
            print(f"Changed to: http://localhost:9999/v1")

# Also try top-level apiBase or baseURL
for field in ["apiBase", "baseURL", "base_url", "api_base"]:
    if field in config:
        old = config[field]
        config[field] = "http://localhost:9999/v1"
        print(f"\nTop-level {field}: {old} -> http://localhost:9999/v1")

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print("\nConfig updated! Force stop and reopen BruceClaw app.")
print("The app will now use the bridge as its LLM proxy.")
print("The bridge adds the system prompt with all capabilities before sending to the real LLM.")
