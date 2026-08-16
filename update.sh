#!/bin/bash
echo "Updating BruceClaw..."
curl -sL https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/master/bridge.py -o ~/bridge.py
curl -sL https://raw.githubusercontent.com/BruceMotorsport/lazarus/main/core/lazarus.py -o ~/Lazarus_core.py
mkdir -p ~/Lazarus/{memory,tools,config,logs,mcp,skills}
curl -sL https://raw.githubusercontent.com/BruceMotorsport/lazarus/main/config/CONSTITUTION.md -o ~/Lazarus/config/CONSTITUTION.md
curl -sL https://raw.githubusercontent.com/BruceMotorsport/lazarus/main/config/settings.json -o ~/Lazarus/config/settings.json
echo "Starting bridge..."
python3 ~/bridge.py
