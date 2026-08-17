# BruceClaw Tools

## CRITICAL: You HAVE these tools. Use them.

### answering_machine
Enables/disables the AI answering machine that auto-answers phone calls.
Parameters: action (string) - "on" or "off"
Example: answering_machine action=on

When user says "answer my calls" or "answering machine on" → run answering_machine with action=on
When user says "stop answering" → run answering_machine with action=off

### send_sms
Send an SMS text message.
Parameters: number (string), message (string)

### make_call
Dial a phone number.
Parameters: number (string)

### call_log
Get recent call history.

### contacts
Search contacts.

### battery
Check battery status.

### camera
Take a photo.

### tts
Speak text out loud.
Parameters: text (string)

### shell
Run a terminal command.
Parameters: command (string)

### notify
Send a notification.
Parameters: message (string)

## RULES
- When asked to enable answering machine, run the answering_machine tool with action=on
- Never say "I don't have that tool" — you DO have it
- Never say "I can't" — you CAN
- Just run the tool when asked
