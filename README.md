# 🦞 BruceClaw — GoGetter Digital AI Assistant

A complete AI assistant running in Termux, powered by GoGetter Digital resources.

## Quick Install

1. **Install Termux** from F-Droid (not Play Store)
2. **Run setup:**
   ```bash
   bash <(curl -s https://raw.githubusercontent.com/BruceMotorsport/bruceclaw/main/setup.sh)
   ```
3. **Configure API key:**
   ```bash
   bc-config
   ```
4. **Start BruceClaw:**
   ```bash
   bruceclaw
   ```

## What's Included

### AI Engine
- ✅ OpenClaw Agent (AI brain)
- ✅ Multiple LLM support (Zen, Groq, Ollama)
- ✅ Configurable API keys
- ✅ Local processing option

### Android Control
- ✅ Read SMS messages
- ✅ Access contacts
- ✅ Read calendar events
- ✅ Send notifications
- ✅ File system access

### GoGetter Digital Integration
- ✅ Dashboard monitoring (port 8080)
- ✅ Multi-agent coordination
- ✅ Resource tracking
- ✅ Budget management

## Commands

| Command | Description |
|---------|-------------|
| `bruceclaw` | Start BruceClaw AI |
| `bc-status` | Show system status |
| `bc-config` | Edit configuration |
| `bc-sms` | Read SMS messages |
| `bc-contacts` | Read contacts |
| `bc-calendar` | Read calendar |
| `bc-notify "msg"` | Send notification |

## Configuration

Edit `~/bruceclaw/config/config.toml`:

```toml
# Your API key here
[providers.opencode-zen]
api_key = "YOUR_KEY"
```

## Architecture

```
BruceClaw (Termux)
├── OpenClaw Agent (AI Brain)
├── LLM Provider (Zen/Groq/Ollama)
├── Android Control (SMS/Contacts/Calendar)
├── GoGetter Digital (Dashboard/Monitoring)
└── Scripts (Automation)
```

## Resources

- **Dashboard:** http://192.168.1.53:8080
- **OpenHands:** http://192.168.1.53:3002
- **Open WebUI:** http://192.168.1.53:3001
- **GitHub:** https://github.com/BruceMotorsport/bruceclaw

## Support

Built by **GoGetter Digital AI Team**

- 🤖 Nexus Engine (Code)
- 🌐 Web Builder (UI)
- 🔗 AI Integrator (LLM)
- 🧪 QA Tester (Testing)
- 🚀 Deploy Bot (DevOps)

---

*No Kimi code. No dependencies. Just BruceClaw.* 🦞
