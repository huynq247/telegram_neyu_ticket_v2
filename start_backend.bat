@echo off
REM TelegramNeyu Backend Startup Script
REM Author: GitHub Copilot
REM Version: 1.0.0

echo ====================================================
echo 🚀 TelegramNeyu Backend Startup Script
echo ====================================================

REM Check if virtual environment exists
if not exist "telegram_neyu_env\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run setup_environment.bat first
    pause
    exit /b 1
)

REM Change to project directory
cd /d "%~dp0"

echo 📁 Current directory: %CD%
echo 🔧 Activating virtual environment...

REM Activate virtual environment
call telegram_neyu_env\Scripts\activate.bat

REM Check if activation was successful
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env configuration file not found!
    echo Please create .env file with your configuration
    pause
    exit /b 1
)

echo ✅ Configuration file found

REM Display startup message
echo.
echo 🤖 Starting Telegram Bot Backend...
echo 🔗 PostgreSQL Database Integration
echo 📱 Bot: @ITS247_bot
echo.
echo Press Ctrl+C to stop the backend
echo ====================================================

REM Start the backend
python main.py

REM Handle exit
echo.
echo 👋 Backend stopped
pause