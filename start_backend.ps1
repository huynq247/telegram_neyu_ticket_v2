# TelegramNeyu Backend Startup Script for PowerShell
# Author: GitHub Copilot
# Version: 1.0.0

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "🚀 TelegramNeyu Backend Startup Script" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan

# Get script location
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptPath

# Check if virtual environment exists
if (-not (Test-Path "telegram_neyu_env\Scripts\Activate.ps1")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup_environment.ps1 first" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📁 Current directory: $(Get-Location)" -ForegroundColor Blue
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow

# Activate virtual environment
try {
    & "telegram_neyu_env\Scripts\Activate.ps1"
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env configuration file not found!" -ForegroundColor Red
    Write-Host "Please create .env file with your configuration" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Configuration file found" -ForegroundColor Green

# Display startup message
Write-Host ""
Write-Host "🤖 Starting Telegram Bot Backend..." -ForegroundColor Green
Write-Host "🔗 PostgreSQL Database Integration" -ForegroundColor Blue
Write-Host "📱 Bot: @ITS247_bot" -ForegroundColor Magenta
Write-Host ""
Write-Host "Press Ctrl+C to stop the backend" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan

# Start the backend
try {
    python main.py
}
catch {
    Write-Host "❌ Error starting backend:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
finally {
    Write-Host ""
    Write-Host "👋 Backend stopped" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
}