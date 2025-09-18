"""
Start Handler Module
Handles basic commands: /start, /help
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ..utils.formatters import BotFormatters
from ..utils.keyboards import BotKeyboards

logger = logging.getLogger(__name__)

class StartHandler:
    """Class to handle start and help commands"""
    
    def __init__(self):
        self.formatters = BotFormatters()
        self.keyboards = BotKeyboards()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        welcome_message = self.formatters.format_welcome_message(user.first_name)
        
        await update.message.reply_text(welcome_message)
        logger.info(f"User {user.id} ({user.username}) started using the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_text = self.formatters.format_help_message()
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /menu command - show main menu"""
        keyboard = self.keyboards.get_main_menu_keyboard()
        
        await update.message.reply_text(
            "📱 *Main Menu*\n\nSelect the function you want to use:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )