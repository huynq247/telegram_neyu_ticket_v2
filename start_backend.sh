#!/bin/bash
# TelegramNeyu Backend Startup Script for Linux/Mac
# Author: GitHub Copilot
# Version: 1.0.0

echo "===================================================="
echo "🚀 TelegramNeyu Backend Startup Script"
echo "===================================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "telegram_neyu_env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create virtual environment first:"
    echo "python -m venv telegram_neyu_env"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "🔧 Activating virtual environment..."

# Activate virtual environment
source telegram_neyu_env/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env configuration file not found!"
    echo "Please create .env file with your configuration"
    exit 1
fi

echo "✅ Configuration file found"

# Display startup message
echo ""
echo "🤖 Starting Telegram Bot Backend..."
echo "🔗 PostgreSQL Database Integration"
echo "📱 Bot: @ITS247_bot"
echo ""
echo "Press Ctrl+C to stop the backend"
echo "===================================================="

# Start the backend
python main.py

# Handle exit
echo ""
echo "👋 Backend stopped"
read -p "Press Enter to continue..."