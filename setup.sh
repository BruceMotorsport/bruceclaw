#!/bin/bash
echo "Installing BruceClaw..."
pkg update -y && pkg install -y curl git python nodejs termux-api
npm install -g openclaw
openclaw setup
echo "Done! Type 'openclaw' to start"
