# BruceClaw — AI Assistant for Android

## What is BruceClaw?
A native Android AI assistant that connects to OpenClaw running in Termux. Chat with AI using text, voice, or images.

## Features
- 💬 **Chat** — Big text, dark theme, easy to read
- 🎤 **Voice Input** — Tap mic, speak your message
- 🔊 **Voice Output** — AI reads responses aloud (TTS)
- 📷 **Camera** — Take photos, AI describes what it sees
- ⚙️ **Settings** — Configure server URL, API key, model
- 🌙 **Dark Theme** — Easy on the eyes

## Installation

### Prerequisites
1. **Termux** — Install from F-Droid (NOT Play Store)
   - https://f-droid.org/packages/com.termux/
2. **Termux:API** — Install from F-Droid
   - https://f-droid.org/packages/com.termux.api/

### Install BruceClaw
1. Download `BruceClaw.apk` from the releases
2. Enable "Install from unknown sources" in Android settings
3. Install the APK

### Setup OpenClaw
1. Open Termux
2. Run: `pkg update -y && pkg install -y curl git python nodejs termux-api`
3. Run: `npm install -g openclaw`
4. Run: `openclaw setup`
5. Run: `openclaw` (keep this running)

### Connect BruceClaw
1. Open BruceClaw app
2. Tap ⚙ (settings)
3. Enter your server URL (default: `http://localhost:11434`)
4. Enter your API key (if required)
5. Enter model name (default: `mimo-v2.5`)
6. Tap Save
7. Start chatting!

## Usage

### Chat
Type a message and tap Send (➤)

### Voice
Tap 🎤, speak your message, it sends automatically

### Camera
Tap 📷, take a photo, AI analyzes it

### Settings
Tap ⚙ to configure:
- Server URL
- API Key
- Model name
- Voice on/off

## Troubleshooting

### App crashes on install
- Uninstall any previous BruceClaw version first
- Make sure you have Android 8.0+

### "Error: Connection refused"
- Make sure OpenClaw is running in Termux
- Check the server URL in settings

### Voice not working
- Install Termux:API from F-Droid
- Grant microphone permission

### Camera not working
- Grant camera permission when prompted

## Technical Details
- **Package:** com.gogetter.bruceclaw
- **Min Android:** 8.0 (API 26)
- **Target Android:** 14 (API 34)
- **Size:** ~10MB
- **Dependencies:** OkHttp, AndroidX, Material Design

## License
Proprietary — GoGetter Digital

---

Built by GoGetter Digital AI Team 🦞
