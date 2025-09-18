# Quick fix script to add authentication imports and initialization
import re

# Read the current file
with open('src/telegram_bot/bot_handler.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports after existing imports
import_pattern = r'(from telegram\.ext import.*?\n)'
import_replacement = r'\1\n# Import authentication services\nfrom .services.auth_service import OdooAuthService\nfrom .handlers.auth_handler import AuthHandler\n'

if 'from .services.auth_service import OdooAuthService' not in content:
    content = re.sub(import_pattern, import_replacement, content, flags=re.DOTALL)

# Add authentication initialization after self.application = None
init_pattern = r'(\s+self\.application = None\n)'
init_replacement = r'''\1
        # Initialize authentication service
        odoo_url = f"http://{odoo_config['host']}:{odoo_config['port']}"
        self.auth_service = OdooAuthService(odoo_url, odoo_config['database'])
        self.auth_handler = AuthHandler(self.auth_service)
'''

if 'self.auth_service = OdooAuthService' not in content:
    content = re.sub(init_pattern, init_replacement, content)

# Write back the file
with open('src/telegram_bot/bot_handler.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Authentication imports and initialization added!")