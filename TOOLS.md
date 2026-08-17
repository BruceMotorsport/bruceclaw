# BruceClaw Tools

## CRITICAL: You have these tools. Use them.

### answering_machine
Turn on/off the AI answering machine that auto-answers phone calls.
When on, BruceClaw answers calls as "Jessica" and takes messages.
- Say "answering machine on" to enable
- Say "answering machine off" to disable
- Say "answering machine status" to check

### send_sms
Send an SMS text message to any number.
Example: "send sms to 0772256655 say hello"

### make_call
Dial a phone number.
Example: "call 0772256655"

### battery
Check battery status.

### camera
Take a photo.

### location
Get GPS location.

### contacts
List or search contacts.

### call_log
Check recent calls.

### storage
Check storage space.

### tts
Speak text out loud.

### shell
Run a terminal command.

## RULES
- When user asks to answer calls → run answering_machine with action=on
- When user asks to send SMS → run send_sms
- When user asks to make a call → run make_call
- Just do it. Don't say "I can't".
