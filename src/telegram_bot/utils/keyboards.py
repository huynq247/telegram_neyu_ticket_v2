"""
Telegram Bot Keyboards Module
Contains all keyboard layouts and button configurations
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class BotKeyboards:
    """Class containing all keyboard layouts"""
    
    @staticmethod
    def get_destination_keyboard():
        """Keyboard for destination selection"""
        keyboard = [
            [InlineKeyboardButton("🇻🇳 Vietnam", callback_data="dest_Vietnam")],
            [InlineKeyboardButton("🇹🇭 Thailand", callback_data="dest_Thailand")],
            [InlineKeyboardButton("🇮🇳 India", callback_data="dest_India")],
            [InlineKeyboardButton("🇵🇭 Philippines", callback_data="dest_Philippines")],
            [InlineKeyboardButton("🇲🇾 Malaysia", callback_data="dest_Malaysia")],
            [InlineKeyboardButton("🇮🇩 Indonesia", callback_data="dest_Indonesia")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_priority_keyboard():
        """Keyboard for priority selection"""
        keyboard = [
            [InlineKeyboardButton("🔴 High", callback_data="priority_high")],
            [InlineKeyboardButton("🟡 Medium", callback_data="priority_medium")],
            [InlineKeyboardButton("🟢 Low", callback_data="priority_low")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation_keyboard():
        """Confirmation keyboard"""
        keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_ticket")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_ticket")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_main_menu_keyboard():
        """Main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("🎫 Create New Ticket", callback_data="menu_new_ticket")],
            [InlineKeyboardButton("📋 View My Tickets", callback_data="menu_my_tickets")],
            [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
        ]
        return InlineKeyboardMarkup(keyboard)