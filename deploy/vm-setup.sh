#!/usr/bin/env bash
# ============================================================================
# ProfAssistant — Azure VM Initial Setup
# ============================================================================
# Run this ONCE on a fresh Ubuntu 22.04/24.04 VM to install Docker and
# prepare the environment. Then use deploy.sh for subsequent deployments.
#
# Usage:
#   ssh azureuser@<VM_IP>
#   curl -fsSL https://raw.githubusercontent.com/<your-repo>/deploy/vm-setup.sh | bash
#   # OR copy this file to the VM and run: bash vm-setup.sh
# ============================================================================
set -euo pipefail

echo "══════════════════════════════════════════════════════════════════"
echo "  ProfAssistant — VM Setup"
echo "══════════════════════════════════════════════════════════════════"

# ── Update system ──────────────────────────────────────────────────────────
echo "[1/4] Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# ── Install Docker ─────────────────────────────────────────────────────────
echo "[2/4] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    echo "  Docker installed. You may need to log out and back in for group changes."
else
    echo "  Docker already installed, skipping."
fi

# ── Install Docker Compose plugin ──────────────────────────────────────────
echo "[3/4] Ensuring Docker Compose plugin..."
if ! docker compose version &> /dev/null 2>&1; then
    sudo apt-get install -y -qq docker-compose-plugin
fi
echo "  $(docker compose version)"

# ── Create app directory ───────────────────────────────────────────────────
echo "[4/4] Creating application directory..."
sudo mkdir -p /opt/profassistant
sudo chown "$USER:$USER" /opt/profassistant

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. Log out and back in (for docker group)"
echo "    2. Copy your project to /opt/profassistant/"
echo "    3. Create /opt/profassistant/.env from .env.example"
echo "    4. Run: cd /opt/profassistant && bash deploy/deploy.sh"
echo "══════════════════════════════════════════════════════════════════"
