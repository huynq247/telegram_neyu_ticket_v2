#!/bin/bash

# setup-redhat-server.sh
# Script to setup RedHat server for deployment

set -e

echo "🚀 Setting up RedHat server for Telegram Bot deployment..."

# Update system
echo "📦 Updating system packages..."
sudo dnf update -y

# Install Docker
echo "🐳 Installing Docker..."
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
echo "📋 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
echo "📦 Installing Git..."
sudo dnf install -y git

# Create deployment directory
echo "📁 Creating deployment directory..."
sudo mkdir -p /opt/telegram-neyu
sudo chown $USER:$USER /opt/telegram-neyu

# Navigate to deployment directory
cd /opt/telegram-neyu

# Clone repository
echo "📥 Cloning repository..."
git clone https://github.com/huynq247/telegram_neyu_ticket_v2.git .

# Copy environment file
echo "⚙️ Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual values!"
fi

# Create necessary directories
mkdir -p logs backup

# Set correct permissions
chmod +x scripts/*.sh

# Install firewall rules (if needed)
echo "🔥 Configuring firewall..."
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

echo "✅ Server setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Run deployment: ./scripts/deploy.sh"
echo "3. Check logs: ./scripts/logs.sh"