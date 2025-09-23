"""
Configuration factory for creating container configuration from settings.
Bridges between Pydantic settings and dependency injection container.
"""
from typing import Dict, Any
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import Settings


class ConfigFactory:
    """Factory for creating container configuration from application settings"""
    
    @staticmethod
    def create_container_config(settings: Settings) -> Dict[str, Any]:
        """Create container configuration from application settings"""
        
        return {
            'database': {
                'host': settings.ODOO_URL.replace('http://', '').replace('https://', '').split(':')[0],
                'port': int(settings.ODOO_URL.split(':')[-1]) if ':' in settings.ODOO_URL else 5432,
                'database': settings.ODOO_DB,
                'username': settings.ODOO_USERNAME,
                'password': settings.ODOO_PASSWORD,
                'min_connections': 5,
                'max_connections': 20
            },
            'telegram': {
                'bot_token': settings.TELEGRAM_BOT_TOKEN,
                'webhook_url': getattr(settings, 'TELEGRAM_WEBHOOK_URL', None),
                'webhook_port': getattr(settings, 'TELEGRAM_WEBHOOK_PORT', 8443)
            },
            'application': {
                'name': settings.APP_NAME,
                'version': settings.APP_VERSION,
                'debug_mode': settings.DEBUG_MODE,
                'environment': getattr(settings, 'ENVIRONMENT', 'production')
            },
            'logging': {
                'level': settings.LOG_LEVEL,
                'file_path': getattr(settings, 'LOG_FILE_PATH', 'logs/app.log'),
                'max_size': getattr(settings, 'LOG_MAX_SIZE', 10485760),
                'backup_count': getattr(settings, 'LOG_BACKUP_COUNT', 5)
            },
            'monitoring': {
                'ticket_check_interval': getattr(settings, 'TICKET_CHECK_INTERVAL', 60)
            }
        }
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """Validate configuration before container initialization"""
        
        # Validate database config
        db_config = config.get('database', {})
        required_db_fields = ['host', 'port', 'database', 'username', 'password']
        
        for field in required_db_fields:
            if not db_config.get(field):
                raise ValueError(f"Database configuration missing required field: {field}")
        
        # Validate telegram config
        telegram_config = config.get('telegram', {})
        if not telegram_config.get('bot_token'):
            raise ValueError("Telegram bot token is required")
        
        # Validate application config
        app_config = config.get('application', {})
        if not app_config.get('name'):
            raise ValueError("Application name is required")
    
    @staticmethod
    def get_test_config() -> Dict[str, Any]:
        """Get configuration for testing (uses in-memory/mock services)"""
        
        return {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass',
                'min_connections': 1,
                'max_connections': 5
            },
            'telegram': {
                'bot_token': 'test_bot_token',
                'webhook_url': None,
                'webhook_port': 8443
            },
            'application': {
                'name': 'TelegramNeyu Test',
                'version': '1.0.0-test',
                'debug_mode': True,
                'environment': 'test'
            },
            'logging': {
                'level': 'DEBUG',
                'file_path': 'test_logs/app.log',
                'max_size': 1048576,
                'backup_count': 2
            },
            'monitoring': {
                'ticket_check_interval': 5
            }
        }