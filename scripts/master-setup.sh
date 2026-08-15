#!/bin/bash
# ============================================
# BruceClaw — Master Setup Script
# Uses ALL GoGetter Digital Resources
# ============================================

echo "🦞 BruceClaw Master Setup"
echo "========================="
echo ""

# Colors
GREEN='\033[0;32m'
ORANGE='\033[0;38;5;208m'
NC='\033[0m'

# ============================================
# PHASE 1: Termux Environment
# ============================================
echo -e "${ORANGE}[Phase 1] Setting up Termux Environment...${NC}"

pkg update -y && pkg upgrade -y
pkg install -y curl wget git python nodejs openssh termux-api

# ============================================
# PHASE 2: OpenClaw AI Agent
# ============================================
echo -e "${ORANGE}[Phase 2] Installing OpenClaw Agent...${NC}"

mkdir -p ~/bruceclaw/{config,logs,data,scripts}
cd ~/bruceclaw

# Clone OpenClaw
git clone https://github.com/openclaw/openclaw.git 2>/dev/null || echo "OpenClaw already installed"
cd openclaw && npm install

# ============================================
# PHASE 3: LLM Configuration
# ============================================
echo -e "${ORANGE}[Phase 3] Configuring LLM Provider...${NC}"

cat > ~/bruceclaw/config/config.toml << 'EOF'
# BruceClaw Configuration
# GoGetter Digital AI Assistant

default_model = "mimo-v2.5"
default_thinking = true
default_yolo = true
default_editor = ""

# OpenCode Zen (Primary)
[models.mimo-v2.5]
provider = "opencode-zen"
model = "mimo-v2.5"
max_context_size = 1000000
capabilities = ["image_in", "thinking"]

[providers.opencode-zen]
type = "openai"
base_url = "https://opencode.ai/zen/go/v1"
api_key = ""

# Groq (Free Fallback)
[models.llama-3.3-70b]
provider = "groq"
model = "llama-3.3-70b-versatile"
max_context_size = 128000

[providers.groq]
type = "openai"
base_url = "https://api.groq.com/openai/v1"
api_key = ""

# Local Ollama (Private)
[models.qwen3-4b]
provider = "ollama"
model = "qwen3:4b"
max_context_size = 32000

[providers.ollama]
type = "openai"
base_url = "http://localhost:11434/v1"
api_key = "ollama"

[loop_control]
max_steps_per_turn = 100
max_retries_per_step = 3
EOF

# ============================================
# PHASE 4: Android Control Scripts
# ============================================
echo -e "${ORANGE}[Phase 4] Setting up Android Control...${NC}"

mkdir -p ~/bruceclaw/scripts

# SMS Reader
cat > ~/bruceclaw/scripts/read-sms.sh << 'SCRIPT'
#!/bin/bash
termux-sms-list -l 10 2>/dev/null || echo "Termux API not available"
SCRIPT
chmod +x ~/bruceclaw/scripts/read-sms.sh

# Contact Reader
cat > ~/bruceclaw/scripts/read-contacts.sh << 'SCRIPT'
#!/bin/bash
termux-contact-list 2>/dev/null || echo "Termux API not available"
SCRIPT
chmod +x ~/bruceclaw/scripts/read-contacts.sh

# Calendar Reader
cat > ~/bruceclaw/scripts/read-calendar.sh << 'SCRIPT'
#!/bin/bash
termux-calendar-list 2>/dev/null || echo "Termux API not available"
SCRIPT
chmod +x ~/bruceclaw/scripts/read-calendar.sh

# Notification Sender
cat > ~/bruceclaw/scripts/notify.sh << 'SCRIPT'
#!/bin/bash
termux-notification -t "BruceClaw" -c "$1" 2>/dev/null || echo "$1"
SCRIPT
chmod +x ~/bruceclaw/scripts/notify.sh

# ============================================
# PHASE 5: GoGetter Digital Integration
# ============================================
echo -e "${ORANGE}[Phase 5] Integrating with GoGetter Digital...${NC}"

# Dashboard URL
cat > ~/bruceclaw/config/dashboard.txt << 'EOF'
http://192.168.1.53:8080
EOF

# API Endpoints
cat > ~/bruceclaw/config/endpoints.txt << 'EOF'
OpenCode Zen: https://opencode.ai/zen/go/v1
OmniRoute: http://192.168.1.53:20128/v1
Groq: https://api.groq.com/openai/v1
Dashboard: http://192.168.1.53:8080
OpenHands: http://192.168.1.53:3002
Open WebUI: http://192.168.1.53:3001
EOF

# ============================================
# PHASE 6: Launchers
# ============================================
echo -e "${ORANGE}[Phase 6] Creating Launchers...${NC}"

# Main launcher
cat > ~/bruceclaw/launch.sh << 'EOF'
#!/bin/bash
cd ~/bruceclaw/openclaw
echo "🦞 BruceClaw — GoGetter Digital AI"
echo "=================================="
echo ""
echo "Commands:"
echo "  /help    - Show help"
echo "  /config  - Edit config"
echo "  /status  - Show status"
echo "  /quit    - Exit"
echo ""
node cli.js --no-update-check
EOF
chmod +x ~/bruceclaw/launch.sh

# Status checker
cat > ~/bruceclaw/status.sh << 'EOF'
#!/bin/bash
echo "🦞 BruceClaw Status"
echo "==================="
echo ""
echo "LLM: $(grep 'default_model' ~/bruceclaw/config/config.toml | cut -d'"' -f2)"
echo "Config: ~/bruceclaw/config/config.toml"
echo "Logs: ~/bruceclaw/logs/"
echo "Dashboard: http://192.168.1.53:8080"
echo ""
echo "Android Control:"
echo "  SMS: termux-sms-list"
echo "  Contacts: termux-contact-list"
echo "  Calendar: termux-calendar-list"
echo "  Notify: termux-notification -t 'Title' -c 'Message'"
EOF
chmod +x ~/bruceclaw/status.sh

# ============================================
# PHASE 7: Aliases
# ============================================
echo -e "${ORANGE}[Phase 7] Setting up aliases...${NC}"

cat >> ~/.bashrc << 'EOF'

# BruceClaw Aliases
alias bruceclaw='bash ~/bruceclaw/launch.sh'
alias bc-status='bash ~/bruceclaw/status.sh'
alias bc-config='nano ~/bruceclaw/config/config.toml'
alias bc-logs='tail -f ~/bruceclaw/logs/*.log'
alias bc-sms='bash ~/bruceclaw/scripts/read-sms.sh'
alias bc-contacts='bash ~/bruceclaw/scripts/read-contacts.sh'
alias bc-calendar='bash ~/bruceclaw/scripts/read-calendar.sh'
alias bc-notify='bash ~/bruceclaw/scripts/notify.sh'

EOF

# ============================================
# DONE
# ============================================
echo ""
echo -e "${GREEN}=========================================="
echo "  🦞 BruceClaw Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Quick Start:"
echo "  bruceclaw        # Start BruceClaw"
echo "  bc-status        # Show status"
echo "  bc-config        # Edit config"
echo "  bc-sms           # Read SMS"
echo "  bc-contacts      # Read contacts"
echo "  bc-calendar      # Read calendar"
echo ""
echo "Configure API key:"
echo "  bc-config"
echo ""
echo "Dashboard:"
echo "  http://192.168.1.53:8080"
echo ""
