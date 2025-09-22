#!/bin/bash

# deploy.sh
# Manual deployment script for RedHat server

set -e

echo "🚀 Deploying Telegram Bot..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy from .env.example and configure."
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build and start containers
echo "🐳 Building and starting containers..."
docker compose down || true
docker compose build --no-cache
docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check container status
echo "📊 Container status:"
docker compose ps

# Show logs
echo "📝 Recent logs:"
docker compose logs --tail=20 telegram-bot

echo "✅ Deployment completed!"
echo ""
echo "Useful commands:"
echo "  View logs: docker compose logs -f telegram-bot"
echo "  Restart: docker compose restart telegram-bot"
echo "  Stop: docker compose down"