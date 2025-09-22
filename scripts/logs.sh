#!/bin/bash

# logs.sh
# Script to view and manage logs

function show_help() {
    echo "📝 Log Management Script"
    echo ""
    echo "Usage: ./logs.sh [option]"
    echo ""
    echo "Options:"
    echo "  -f, --follow     Follow log output (real-time)"
    echo "  -t, --tail N     Show last N lines (default: 50)"
    echo "  -e, --errors     Show only error logs"
    echo "  -c, --clear      Clear old logs"
    echo "  -h, --help       Show this help message"
}

case "$1" in
    -f|--follow)
        echo "📡 Following logs (Ctrl+C to stop)..."
        docker compose logs -f telegram-bot
        ;;
    -t|--tail)
        LINES=${2:-50}
        echo "📋 Showing last $LINES lines..."
        docker compose logs --tail=$LINES telegram-bot
        ;;
    -e|--errors)
        echo "❌ Showing error logs..."
        docker compose logs telegram-bot | grep -i error
        ;;
    -c|--clear)
        echo "🧹 Clearing old logs..."
        docker compose logs --tail=0 telegram-bot
        echo "✅ Logs cleared!"
        ;;
    -h|--help)
        show_help
        ;;
    *)
        echo "📋 Showing last 50 lines of logs..."
        docker compose logs --tail=50 telegram-bot
        ;;
esac