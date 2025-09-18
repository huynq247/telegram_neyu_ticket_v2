"""
Main Application
Entry point cho Telegram Neyu Backend
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Thêm src vào Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.settings import settings, setup_logging, print_settings_info
from src.odoo.postgresql_connector import PostgreSQLConnector
from urllib.parse import urlparse
from src.telegram_bot.bot_handler import TelegramBotHandler
from src.ticket.manager import TicketManager

logger = logging.getLogger(__name__)

class TelegramNeyuApp:
    """Main application class"""
    
    def __init__(self):
        """Khởi tạo ứng dụng"""
        self.pg_connector = None
        self.telegram_handler = None
        self.ticket_manager = None
        self.running = False
    
    def validate_configuration(self) -> bool:
        """
        Validate cấu hình ứng dụng
        
        Returns:
            True nếu cấu hình hợp lệ
        """
        if not settings.validate_settings():
            logger.error("Cấu hình không hợp lệ")
            return False
        
        logger.info("Cấu hình hợp lệ")
        return True
    
    async def initialize_components(self) -> bool:
        """
        Khởi tạo các components
        
        Returns:
            True nếu khởi tạo thành công
        """
        try:
            logger.info("Bắt đầu khởi tạo components...")
            
            # 1. Khởi tạo PostgreSQL Connector
            logger.info("Khởi tạo PostgreSQL Connector...")
            parsed = urlparse(settings.odoo_url)
            self.pg_connector = PostgreSQLConnector(
                host=parsed.hostname,
                port=parsed.port,
                database=settings.odoo_db,
                username=settings.odoo_username,
                password=settings.odoo_password
            )
            
            # Test kết nối PostgreSQL
            if not self.pg_connector.test_connection():
                logger.error("Không thể kết nối tới PostgreSQL")
                return False
            
            logger.info("✅ PostgreSQL Connector khởi tạo thành công")
            
            # 2. Khởi tạo Ticket Manager
            logger.info("Khởi tạo Ticket Manager...")
            self.ticket_manager = TicketManager(self.pg_connector)
            logger.info("✅ Ticket Manager khởi tạo thành công")
            
            # 3. Khởi tạo Telegram Bot Handler
            logger.info("Khởi tạo Telegram Bot Handler...")
            
            # Create Odoo config dict
            odoo_config = {
                'host': settings.odoo_url.split('://')[1].split(':')[0],
                'port': int(settings.odoo_url.split(':')[2]) if ':' in settings.odoo_url.split('://')[1] else 8069,
                'database': settings.odoo_db,
                'username': settings.odoo_username,
                'password': settings.odoo_password
            }
            
            self.telegram_handler = TelegramBotHandler(
                token=settings.telegram_bot_token,
                ticket_manager=self.ticket_manager,
                odoo_config=odoo_config
            )
            
            # Thiết lập liên kết giữa các components
            self.ticket_manager.set_telegram_handler(self.telegram_handler)
            
            # Khởi tạo Telegram Bot
            await self.telegram_handler.initialize()
            logger.info("✅ Telegram Bot Handler khởi tạo thành công")
            
            logger.info("🎉 Tất cả components đã được khởi tạo thành công")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khởi tạo components: {e}")
            return False
    
    async def start_services(self) -> None:
        """Khởi động các services"""
        try:
            logger.info("Khởi động services...")
            
            # Bắt đầu ticket monitoring
            self.ticket_manager.start_monitoring_task(
                check_interval=settings.ticket_check_interval
            )
            
            # Bắt đầu Telegram Bot
            await self.telegram_handler.start_polling()
            
            logger.info("🚀 Tất cả services đã khởi động")
            
        except Exception as e:
            logger.error(f"Lỗi khởi động services: {e}")
            raise
    
    async def stop_services(self) -> None:
        """Dừng các services"""
        try:
            logger.info("Đang dừng services...")
            
            # Dừng ticket monitoring
            if self.ticket_manager:
                self.ticket_manager.stop_monitoring_task()
            
            # Dừng Telegram Bot
            if self.telegram_handler:
                await self.telegram_handler.stop()
            
            logger.info("✅ Tất cả services đã dừng")
            
        except Exception as e:
            logger.error(f"Lỗi dừng services: {e}")
    
    def setup_signal_handlers(self) -> None:
        """Thiết lập signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Nhận signal {signum}, đang thoát...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self) -> None:
        """Chạy ứng dụng"""
        try:
            logger.info("🚀 Khởi động Telegram Neyu Backend...")
            
            # Validate cấu hình
            if not self.validate_configuration():
                return
            
            # Khởi tạo components
            if not await self.initialize_components():
                return
            
            # Thiết lập signal handlers
            self.setup_signal_handlers()
            
            # Khởi động services
            self.running = True
            await self.start_services()
            
            # Chờ đến khi được signal dừng
            logger.info("✅ Ứng dụng đang chạy... (Ctrl+C để dừng)")
            
            try:
                while self.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Nhận KeyboardInterrupt, đang thoát...")
            
        except Exception as e:
            logger.error(f"Lỗi chạy ứng dụng: {e}")
            raise
        
        finally:
            # Dừng services
            await self.stop_services()
            logger.info("👋 Telegram Neyu Backend đã thoát")

async def main():
    """Main function"""
    
    # Thiết lập logging
    setup_logging()
    
    # In thông tin cấu hình
    print_settings_info()
    
    # Tạo và chạy ứng dụng
    app = TelegramNeyuApp()
    
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Ứng dụng bị gián đoạn bởi người dùng")
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Chạy ứng dụng với asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"❌ Lỗi fatal: {e}")
        sys.exit(1)