@echo off
echo Starting Neyu Ticket Bot with Web App...

echo.
echo Installing required packages...
pip install flask flask-cors

echo.
echo Starting Web App server in background...
start "Web App Server" cmd /k "cd /d d:\TelegramNeyu\src\webapp && python app.py"

echo.
echo Waiting for Web App server to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Telegram Bot...
cd /d "d:\TelegramNeyu\src"
python main.py

pause