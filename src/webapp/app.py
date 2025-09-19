"""
Simple Flask server to serve Telegram Web App
"""
from flask import Flask, render_template_string, send_from_directory
import os

app = Flask(__name__)

# Get the webapp directory path
WEBAPP_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """Serve the main login page"""
    with open(os.path.join(WEBAPP_DIR, 'login.html'), 'r', encoding='utf-8') as f:
        content = f.read()
    return content

@app.route('/login')
def login():
    """Alternative route for login page"""
    return index()

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files if needed"""
    return send_from_directory(WEBAPP_DIR, filename)

if __name__ == '__main__':
    print("🌐 Starting Telegram Web App server...")
    print("📱 Web App URL: http://localhost:5000")
    print("🔗 Use this URL in your Telegram Bot Web App button")
    app.run(host='0.0.0.0', port=5000, debug=True)