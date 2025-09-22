#!/bin/bash

# health-check.sh
# Health monitoring script

set -e

echo "🏥 Telegram Bot Health Check"
echo "=========================="

# Check if containers are running
echo "📦 Container Status:"
if docker compose ps | grep -q "Up"; then
    echo "✅ Containers are running"
else
    echo "❌ Some containers are not running"
    docker compose ps
    exit 1
fi

# Check bot connectivity
echo ""
echo "🤖 Bot Connectivity:"
if docker compose exec telegram-bot python -c "
import sys
sys.path.append('/app/src')
try:
    from telegram_bot.bot_handler import TelegramBotHandler
    print('✅ Bot imports successfully')
except Exception as e:
    print(f'❌ Bot import failed: {e}')
    sys.exit(1)
"; then
    echo "✅ Bot is healthy"
else
    echo "❌ Bot health check failed"
    exit 1
fi

# Check database connectivity
echo ""
echo "🗄️ Database Connectivity:"
if docker compose exec postgres pg_isready -U postgres; then
    echo "✅ Database is healthy"
else
    echo "❌ Database health check failed"
    exit 1
fi

# Check disk space
echo ""
echo "💾 Disk Usage:"
df -h /opt/telegram-neyu

# Check memory usage
echo ""
echo "🧠 Memory Usage:"
docker stats --no-stream

echo ""
echo "✅ All health checks passed!"