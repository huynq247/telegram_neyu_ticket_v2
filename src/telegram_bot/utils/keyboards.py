"""
Telegram Bot Keyboards Module
Chứa tất cả keyboard layouts và button configurations
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class BotKeyboards:
    """Class chứa tất cả keyboard layouts"""
    
    @staticmethod
    def get_destination_keyboard():
        """Keyboard chọn điểm đến"""
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
        """Keyboard chọn độ ưu tiên"""
        keyboard = [
            [InlineKeyboardButton("🔴 Cao", callback_data="priority_high")],
            [InlineKeyboardButton("🟡 Trung bình", callback_data="priority_medium")],
            [InlineKeyboardButton("🟢 Thấp", callback_data="priority_low")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation_keyboard():
        """Keyboard xác nhận"""
        keyboard = [
            [InlineKeyboardButton("✅ Xác nhận", callback_data="confirm_ticket")],
            [InlineKeyboardButton("❌ Hủy", callback_data="cancel_ticket")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_main_menu_keyboard():
        """Keyboard menu chính"""
        keyboard = [
            [InlineKeyboardButton("🎫 Tạo Ticket Mới", callback_data="menu_new_ticket")],
            [InlineKeyboardButton("📋 Xem Tickets Của Tôi", callback_data="menu_my_tickets")],
            [InlineKeyboardButton("❓ Trợ Giúp", callback_data="menu_help")]
        ]
        return InlineKeyboardMarkup(keyboard)