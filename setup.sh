#!/bin/bash
echo "Setting up BruceClaw..."
curl -sL https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/master/bridge.py -o ~/bridge.py
echo "Bridge downloaded!"
echo "Starting BruceClaw..."
python3 ~/bridge.py
