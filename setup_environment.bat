@echo off
REM Setup Environment for TelegramNeyu Backend
REM Author: GitHub Copilot
REM This script creates virtual environment and installs dependencies

echo ====================================================
echo 🔧 TelegramNeyu Environment Setup
echo ====================================================

REM Change to project directory
cd /d "%~dp0"

echo 📁 Project directory: %CD%

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist "telegram_neyu_env" (
    echo 🏗️  Creating virtual environment...
    python -m venv telegram_neyu_env
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call telegram_neyu_env\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install python-telegram-bot psycopg2-binary python-dotenv pydantic-settings

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Check if .env exists
if exist ".env" (
    echo ✅ Configuration file (.env) found
) else (
    echo ⚠️  Warning: .env file not found
    echo Please create .env file with your configuration:
    echo TELEGRAM_BOT_TOKEN=your_bot_token
    echo ODOO_URL=your_odoo_url
    echo ODOO_DB=your_database
    echo ODOO_USERNAME=your_username
    echo ODOO_PASSWORD=your_password
)

echo.
echo ====================================================
echo 🎉 Setup completed successfully!
echo ====================================================
echo.
echo To start the backend, run: start_backend.bat
echo.
pause