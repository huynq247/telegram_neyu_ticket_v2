"""
Start Handler Module
Xử lý các lệnh cơ bản: /start, /help
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ..utils.formatters import BotFormatters
from ..utils.keyboards import BotKeyboards

logger = logging.getLogger(__name__)

class StartHandler:
    """Class xử lý các lệnh start và help"""
    
    def __init__(self):
        self.formatters = BotFormatters()
        self.keyboards = BotKeyboards()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /start"""
        user = update.effective_user
        welcome_message = self.formatters.format_welcome_message(user.first_name)
        
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} ({user.username}) bắt đầu sử dụng bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /help"""
        help_text = self.formatters.format_help_message()
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Xử lý lệnh /menu - hiển thị menu chính"""
        keyboard = self.keyboards.get_main_menu_keyboard()
        
        await update.message.reply_text(
            "📱 *Menu Chính*\n\nChọn chức năng bạn muốn sử dụng:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )