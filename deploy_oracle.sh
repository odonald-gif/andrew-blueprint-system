#!/bin/bash
# Project Andrew: OCI ARM Instantiation Script
# This script configures a VM.Standard.A1.Flex instance for Andrew's self-hosted intelligence.

set -e

echo "[ANDREW] Initializing Free-Tier Oracle ARM Deployment..."

# 1. Update and install core dependencies
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# 2. Install Docker & Docker Compose
echo "[ANDREW] Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo chmod 666 /var/run/docker.sock || true

echo "[ANDREW] Installing Docker Compose..."
sudo apt-get install docker-compose-plugin -y

# 3. Pull Ollama for ARM
echo "[ANDREW] Installing Ollama (Local Brain)..."
curl -fsSL https://ollama.com/install.sh | sh

# 4. Tailscale (VPN for Mobile App to Server Connection)
echo "[ANDREW] Installing Tailscale for Secure Flutter Routing..."
curl -fsSL https://tailscale.com/install.sh | sh

echo "========================================================="
echo "Deployment Baseline Complete."
echo "NEXT STEPS:"
echo "1. Run: sudo tailscale up"
echo "2. CD into your project directory and run: docker-compose up -d --build"
echo "3. Run: ollama pull llama3"
echo "========================================================="
