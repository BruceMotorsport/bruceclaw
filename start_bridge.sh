#!/bin/bash
# BruceClaw Bridge - Non-killable with auto-restart
pkill -f bridge.py 2>/dev/null
sleep 1
termux-wake-lock
cd ~
curl -SL https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/master/bridge_final.py -o bridge.py
curl -SL https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/master/tools.json -o tools.json
termux-notification -t "BruceClaw" -c "Bridge starting..." --id bruceclaw --priority low
while true; do
    python3 ~/bridge.py
    echo "Bridge crashed, restarting in 3 seconds..."
    sleep 3
done
