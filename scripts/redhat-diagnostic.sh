#!/bin/bash
# RedHat Server Troubleshooting Script
# Run this script on your RedHat server to diagnose deployment issues

echo "🔍 TELEGRAM NEYU DEPLOYMENT DIAGNOSTICS"
echo "========================================"

echo ""
echo "📁 1. Checking deployment directory..."
if [ -d "/opt/telegram-neyu" ]; then
    echo "✅ /opt/telegram-neyu exists"
    cd /opt/telegram-neyu
    
    echo ""
    echo "📋 Git status:"
    git status --porcelain
    
    echo ""
    echo "🔍 Latest commits:"
    git log --oneline -5
    
    echo ""
    echo "🌿 Current branch:"
    git branch --show-current
else
    echo "❌ /opt/telegram-neyu directory not found!"
    echo "🔧 Need to setup: git clone https://github.com/huynq247/telegram_neyu_ticket_v2.git /opt/telegram-neyu"
fi

echo ""
echo "🐳 2. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    
    echo ""
    echo "📦 Running containers:"
    docker compose ps
    
    echo ""
    echo "🖼️ Available images:"
    docker images | grep -E "(telegram|neyu|ghcr.io)"
    
    echo ""
    echo "📄 Recent logs:"
    docker compose logs telegram-bot --tail=10
else
    echo "❌ Docker not found!"
fi

echo ""
echo "🔐 3. Checking GitHub Container Registry access..."
if docker info | grep -q "ghcr.io"; then
    echo "✅ Logged into GitHub Container Registry"
else
    echo "⚠️ Not logged into GitHub Container Registry"
    echo "🔧 Need to run: echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
fi

echo ""
echo "🌐 4. Checking environment variables..."
if [ -f "/opt/telegram-neyu/.env" ]; then
    echo "✅ .env file exists"
    echo "📋 Environment variables (without values):"
    grep -E "^[A-Z_]+" /opt/telegram-neyu/.env | cut -d'=' -f1
else
    echo "❌ .env file not found!"
    echo "🔧 Need to create .env file with required variables"
fi

echo ""
echo "🔧 5. Quick fix commands:"
echo "==============================================="
echo "# If git is behind:"
echo "cd /opt/telegram-neyu && git pull origin main"
echo ""
echo "# If containers are not running:"
echo "cd /opt/telegram-neyu && docker compose up -d"
echo ""
echo "# If need to rebuild:"
echo "cd /opt/telegram-neyu && docker compose down && docker compose up -d --build"
echo ""
echo "# If need to login to GitHub Registry:"
echo "echo \$GITHUB_TOKEN | docker login ghcr.io -u huynq247 --password-stdin"
echo ""
echo "# Check logs:"
echo "cd /opt/telegram-neyu && docker compose logs -f telegram-bot"