#!/bin/bash
# BruceClaw — Termux Setup Script
# Run this in Termux to set up BruceClaw

echo "=========================================="
echo "  BruceClaw — AI Assistant Setup"
echo "=========================================="
echo ""

# Update packages
echo "[1/6] Updating packages..."
pkg update -y && pkg upgrade -y

# Install dependencies
echo "[2/6] Installing dependencies..."
pkg install -y curl wget git python nodejs openssh

# Create BruceClaw directory
echo "[3/6] Setting up BruceClaw..."
mkdir -p ~/bruceclaw
cd ~/bruceclaw

# Download OpenClaw
echo "[4/6] Installing OpenClaw..."
git clone https://github.com/openclaw/openclaw.git
cd openclaw
npm install

# Create config
echo "[5/6] Creating config..."
cat > ~/bruceclaw/config.toml << 'EOF'
default_model = "mimo-v2.5"
default_thinking = true
default_yolo = true
default_editor = ""

[models.mimo-v2.5]
provider = "opencode-zen"
model = "mimo-v2.5"
max_context_size = 1000000
capabilities = ["image_in", "thinking"]

[providers.opencode-zen]
type = "openai"
base_url = "https://opencode.ai/zen/go/v1"
api_key = ""

[loop_control]
max_steps_per_turn = 100
max_retries_per_step = 3
EOF

# Create launcher
echo "[6/6] Creating launcher..."
cat > ~/bruceclaw/launch.sh << 'EOF'
#!/bin/bash
cd ~/bruceclaw/openclaw
echo "Starting BruceClaw..."
echo "Type your message and press Enter"
echo "Type /quit to exit"
echo ""
node cli.js --no-update-check
EOF
chmod +x ~/bruceclaw/launch.sh

# Create alias
echo 'alias bruceclaw="bash ~/bruceclaw/launch.sh"' >> ~/.bashrc

echo ""
echo "=========================================="
echo "  BruceClaw Setup Complete!"
echo "=========================================="
echo ""
echo "To start BruceClaw:"
echo "  bruceclaw"
echo ""
echo "Or:"
echo "  bash ~/bruceclaw/launch.sh"
echo ""
echo "Configure your API key:"
echo "  nano ~/bruceclaw/config.toml"
echo ""
