"""
Application bootstrap module.
Initializes and starts the application with proper dependency injection.
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from .container import initialize_container, cleanup_container, get_container
from .config.container_config import ConfigFactory
from config.settings import get_settings

logger = logging.getLogger(__name__)


class Application:
    """Main application class with clean architecture setup"""
    
    def __init__(self):
        self.container = None
        self.running = False
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the application with full dependency injection"""
        try:
            logger.info("🚀 Starting TelegramNeyu with Clean Architecture...")
            
            # Load settings
            settings = get_settings()
            logger.info(f"📋 Loaded settings for environment: {getattr(settings, 'ENVIRONMENT', 'production')}")
            
            # Create container configuration
            config = ConfigFactory.create_container_config(settings)
            ConfigFactory.validate_config(config)
            
            # Initialize dependency container
            logger.info("🔧 Initializing dependency container...")
            self.container = await initialize_container(config)
            
            # Health check
            health = await self.container.health_check()
            logger.info(f"💓 Health check: {health}")
            
            if not health.get('overall', False):
                raise RuntimeError("Application health check failed")
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start Telegram bot (this would be implemented based on your bot setup)
            await self._start_telegram_bot(config['telegram'])
            
            self.running = True
            logger.info("✅ Application started successfully!")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Failed to start application: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _start_telegram_bot(self, telegram_config: dict) -> None:
        """Start the Telegram bot with dependency injection"""
        # TODO: Implement Telegram bot startup with new architecture
        # This would integrate with the existing bot setup but use the new handlers
        
        logger.info("🤖 Starting Telegram bot...")
        
        # Get handlers from container
        comment_handler = self.container.get_comment_handler()
        
        # TODO: Setup conversation handlers, commands, etc.
        # For now, just log that the bot would start
        logger.info("🤖 Telegram bot handlers configured with clean architecture")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        if sys.platform != "win32":
            # Unix/Linux signal handling
            loop = asyncio.get_running_loop()
            
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, self._signal_handler, sig)
        else:
            # Windows signal handling
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame=None) -> None:
        """Handle shutdown signals"""
        logger.info(f"📨 Received signal {signum}, initiating graceful shutdown...")
        if not self._shutdown_event.is_set():
            self._shutdown_event.set()
    
    async def _cleanup(self) -> None:
        """Cleanup application resources"""
        logger.info("🧹 Cleaning up application resources...")
        
        try:
            if self.container:
                await cleanup_container()
                self.container = None
            
            self.running = False
            logger.info("✅ Application cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    async def stop(self) -> None:
        """Stop the application gracefully"""
        if self.running:
            logger.info("🛑 Stopping application...")
            self._shutdown_event.set()


class DevelopmentApplication(Application):
    """Development version with additional debugging features"""
    
    async def start(self) -> None:
        """Start with development features"""
        logger.info("🔧 Starting in DEVELOPMENT mode...")
        
        # Add development-specific setup
        logging.getLogger().setLevel(logging.DEBUG)
        
        # Call parent start
        await super().start()
    
    async def _start_telegram_bot(self, telegram_config: dict) -> None:
        """Start bot with development features"""
        logger.info("🔧 Starting Telegram bot in development mode...")
        
        # Add development-specific bot setup
        await super()._start_telegram_bot(telegram_config)


class TestApplication(Application):
    """Test version for unit/integration testing"""
    
    def __init__(self):
        super().__init__()
        self.test_mode = True
    
    async def start(self) -> None:
        """Start with test configuration"""
        logger.info("🧪 Starting in TEST mode...")
        
        # Use test configuration instead of loading from settings
        config = ConfigFactory.get_test_config()
        ConfigFactory.validate_config(config)
        
        # Initialize with test config
        self.container = await initialize_container(config)
        
        # Skip signal handlers and bot startup in test mode
        self.running = True
        logger.info("✅ Test application started")
    
    async def _start_telegram_bot(self, telegram_config: dict) -> None:
        """Skip bot startup in test mode"""
        logger.info("🧪 Skipping Telegram bot startup in test mode")


async def create_application(mode: str = "production") -> Application:
    """Factory function to create application based on mode"""
    
    if mode == "development":
        return DevelopmentApplication()
    elif mode == "test":
        return TestApplication()
    else:
        return Application()


async def run_application() -> None:
    """Main entry point for running the application"""
    
    # Determine mode from environment or arguments
    mode = "production"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    # Create and start application
    app = await create_application(mode)
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"💥 Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the application
    asyncio.run(run_application())