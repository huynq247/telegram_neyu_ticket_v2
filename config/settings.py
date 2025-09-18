"""
Configuration Module
Quản lý cấu hình và môi trường cho ứng dụng
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# Load environment variables từ file .env
load_dotenv()

class Settings(BaseSettings):
    """Class cấu hình ứng dụng"""
    
    # Telegram Bot settings
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    telegram_webhook_port: int = Field(8443, env="TELEGRAM_WEBHOOK_PORT")
    
    # Odoo settings
    odoo_url: str = Field(..., env="ODOO_URL")
    odoo_db: str = Field(..., env="ODOO_DB")
    odoo_username: str = Field(..., env="ODOO_USERNAME")
    odoo_password: str = Field(..., env="ODOO_PASSWORD")
    
    # Application settings
    app_name: str = Field("TelegramNeyu", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    
    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file_path: str = Field("logs/app.log", env="LOG_FILE_PATH")
    log_max_size: int = Field(10 * 1024 * 1024, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    
    # Ticket monitoring settings
    ticket_check_interval: int = Field(60, env="TICKET_CHECK_INTERVAL")  # seconds
    
    # Database settings (nếu cần local database)
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def validate_settings(self) -> bool:
        """
        Validate các settings bắt buộc
        
        Returns:
            True nếu tất cả settings hợp lệ
        """
        required_fields = [
            'telegram_bot_token',
            'odoo_url',
            'odoo_db', 
            'odoo_username',
            'odoo_password'
        ]
        
        for field in required_fields:
            if not getattr(self, field, None):
                print(f"ERROR: Thiếu cấu hình bắt buộc: {field}")
                return False
        
        return True

# Global settings instance
settings = Settings()

def setup_logging() -> None:
    """Thiết lập logging cho ứng dụng"""
    
    # Tạo thư mục logs nếu chưa tồn tại
    log_dir = os.path.dirname(settings.log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Cấu hình logging level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Cấu hình formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # File handler với rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        filename=settings.log_file_path,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Xóa handlers cũ và thêm handlers mới
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Thiết lập level cho các logger cụ thể
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Log khởi tạo
    logger = logging.getLogger(__name__)
    logger.info(f"Logging đã được thiết lập - Level: {settings.log_level}")
    logger.info(f"Log file: {settings.log_file_path}")

def get_settings() -> Settings:
    """
    Lấy settings instance
    
    Returns:
        Settings instance
    """
    return settings

def print_settings_info() -> None:
    """In thông tin cấu hình (ẩn thông tin nhạy cảm)"""
    print("=" * 50)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("=" * 50)
    print(f"📊 Debug Mode: {settings.debug_mode}")
    print(f"📝 Log Level: {settings.log_level}")
    print(f"📂 Log File: {settings.log_file_path}")
    print(f"🔗 Odoo URL: {settings.odoo_url}")
    print(f"🗄️  Odoo DB: {settings.odoo_db}")
    print(f"👤 Odoo User: {settings.odoo_username}")
    print(f"🤖 Telegram Bot: {'✅ Configured' if settings.telegram_bot_token else '❌ Not configured'}")
    if settings.telegram_webhook_url:
        print(f"🪝 Webhook URL: {settings.telegram_webhook_url}")
        print(f"🔌 Webhook Port: {settings.telegram_webhook_port}")
    else:
        print("📊 Polling Mode: Enabled")
    print(f"⏱️  Check Interval: {settings.ticket_check_interval}s")
    print("=" * 50)

if __name__ == "__main__":
    # Test cấu hình
    setup_logging()
    
    if settings.validate_settings():
        print("✅ Cấu hình hợp lệ")
        print_settings_info()
    else:
        print("❌ Cấu hình không hợp lệ")
        exit(1)