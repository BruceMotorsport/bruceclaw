#!/bin/bash
# BruceClaw Production Bridge - Self-healing with watchdog
# Layer 1: while loop restarts on crash
# Layer 2: termux-wake-lock prevents Android kill
# Layer 3: persistent notification shows status

# Kill old instances
pkill -f bridge.py 2>/dev/null
pkill -f start_bridge 2>/dev/null
sleep 1

# Keep phone awake
termux-wake-lock

# Download latest bridge
cd ~
curl -SL https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/master/bridge_final.py -o bridge.py 2>/dev/null
curl -SL https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/master/tools.json -o tools.json 2>/dev/null

# Start bridge with auto-restart
echo "BruceClaw Production Bridge starting..."
while true; do
    # Update notification - bridge is starting
    termux-notification --title "BruceClaw" --content "Starting bridge..." --id bruceclaw --priority low 2>/dev/null
    
    # Run bridge
    python3 ~/bridge.py 2>&1
    
    # If bridge exits, wait and restart
    echo "$(date): Bridge crashed, restarting in 2 seconds..."
    sleep 2
done
