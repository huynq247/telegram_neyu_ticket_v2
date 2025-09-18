#!/bin/bash
# Script để chạy ứng dụng trên Linux/Mac
echo "Starting Telegram Neyu Backend..."
cd "$(dirname "$0")"
source telegram_neyu_env/bin/activate
python main.py