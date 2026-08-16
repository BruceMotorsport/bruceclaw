#!/bin/bash
while true; do
  termux-notification -t "BruceClaw" -c "Bridge running - tap to open" --action "termux-open"
  sleep 300
done
