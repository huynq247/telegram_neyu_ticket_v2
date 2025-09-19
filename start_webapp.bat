@echo off
echo Installing Flask for Web App...
pip install flask flask-cors

echo.
echo Starting Web App server...
cd /d "d:\TelegramNeyu\src\webapp"
python app.py