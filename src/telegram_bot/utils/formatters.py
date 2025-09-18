"""
Telegram Bot Formatters Module
Chứa các function format message và text
"""
from typing import Dict, Any

class BotFormatters:
    """Class chứa các formatting methods"""
    
    # Emoji mapping cho destinations
    DESTINATION_EMOJIS = {
        'Vietnam': '🇻🇳',
        'Thailand': '🇹🇭', 
        'India': '🇮🇳',
        'Philippines': '🇵🇭',
        'Malaysia': '🇲🇾',
        'Indonesia': '🇮🇩'
    }
    
    # Priority mapping
    PRIORITY_MAP = {
        'priority_high': (3, '🔴 High'),
        'priority_medium': (2, '🟡 Medium'),
        'priority_low': (1, '🟢 Low')
    }
    
    # Status emojis
    STATUS_EMOJIS = {
        'new': '🆕',
        'assigned': '👤',
        'solved': '✅',
        'closed': '🔒'
    }
    
    # Priority emojis
    PRIORITY_EMOJIS = {
        0: '⚫',
        1: '🟢',
        2: '🟡',
        3: '🔴'
    }
    
    @staticmethod
    def format_welcome_message(first_name: str) -> str:
        """Format welcome message"""
        return (
            f"Welcome {first_name}! 👋\n"
            "I'm a support ticket bot.\n"
            "Use the following commands:\n\n"
            "/newticket - Create new ticket\n"
            "/mytickets - View your tickets\n"
            "/help - Help guide"
        )
    
    @staticmethod
    def format_help_message() -> str:
        """Format help message"""
        return (
            "📋 *Bot Usage Guide*\n\n"
            "🆕 */newticket* - Create new support ticket\n"
            "📝 */mytickets* - View your ticket list\n"
            "❓ */help* - Show this guide\n\n"
            "💡 *How to create a ticket:*\n"
            "1. Type /newticket\n"
            "2. Select destination\n"
            "3. Enter problem description\n"
            "4. Choose priority level\n"
            "5. Confirm ticket creation\n\n"
            "✅ You will receive notifications when your ticket is processed!"
        )
    
    @staticmethod
    def format_destination_selection() -> str:
        """Format destination selection message"""
        return (
            "🌍 *Select ticket destination:*\n\n"
            "Please choose the country/region where you need support:"
        )
    
    @staticmethod
    def format_destination_selected(destination: str) -> str:
        """Format destination selected message"""
        emoji = BotFormatters.DESTINATION_EMOJIS.get(destination, '🌍')
        return (
            f"✅ Selected: {emoji} *{destination}*\n\n"
            "📝 Please enter a detailed description of your problem:"
        )
    
    @staticmethod
    def format_priority_selection() -> str:
        """Format priority selection message"""
        return (
            "⚡ *Select ticket priority:*\n\n"
            "🔴 *High* - Urgent issue, needs immediate attention\n"
            "🟡 *Medium* - Important issue, handle within the day\n"
            "🟢 *Low* - Regular issue, handle when available"
        )
    
    @staticmethod
    def format_ticket_confirmation(user_data: Dict[str, Any], priority_text: str) -> str:
        """Format ticket confirmation message"""
        destination = user_data.get('destination', 'Vietnam')
        emoji = BotFormatters.DESTINATION_EMOJIS.get(destination, '🌍')
        
        return (
            "📋 *Confirm ticket information:*\n\n"
            f"👤 *Created by:* {user_data['first_name']}\n"
            f"🌍 *Destination:* {emoji} {destination}\n"
            f"📝 *Description:* {user_data['description']}\n"
            f"⚡ *Priority:* {priority_text}\n\n"
            "Confirm ticket creation?"
        )
    
    @staticmethod
    def format_ticket_success(result: Dict[str, Any], user_data: Dict[str, Any]) -> str:
        """Format ticket creation success message"""
        destination = user_data.get('destination', 'Vietnam')
        emoji = BotFormatters.DESTINATION_EMOJIS.get(destination, '🌍')
        
        ticket_number = result.get('ticket_number', f"#{result['ticket_id']}")
        ticket_name = result.get('ticket_name', 'From Telegram')
        destination_code = result.get('destination_code', destination[:2].upper())
        
        return (
            "✅ *Ticket created successfully!*\n\n"
            f"🎫 *Ticket ID:* `{ticket_number}`\n"
            f"📝 *Title:* {ticket_name}\n"
            f"🌍 *Destination:* {emoji} {destination} ({destination_code})\n"
            f"📄 *Description:* {user_data['description'][:100]}...\n\n"
            "We will process and notify you of the results as soon as possible!"
        )
    
    @staticmethod
    def format_ticket_error(error_message: str) -> str:
        """Format ticket creation error message"""
        return (
            "❌ *Lỗi tạo ticket!*\n\n"
            f"📝 *Lỗi:* {error_message}\n\n"
            "Vui lòng thử lại sau hoặc liên hệ admin."
        )
    
    @staticmethod
    def format_tickets_list(tickets: list) -> str:
        """Format tickets list message"""
        if not tickets:
            return (
                "📋 You don't have any tickets yet.\n"
                "Use /newticket to create a new ticket."
            )
        
        message = "📋 *Your tickets list:*\n\n"
        
        for ticket in tickets[-10:]:  # Show 10 most recent tickets
            status_emoji = BotFormatters.STATUS_EMOJIS.get(
                ticket.get('stage', 'new'), '❓'
            )
            priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
                ticket.get('priority', 1), '🟡'
            )
            
            message += (
                f"{status_emoji} *{ticket.get('name', 'Unknown')}*\n"
                f"🎫 `{ticket.get('ticket_number', 'N/A')}`\n"
                f"{priority_emoji} Priority: {ticket.get('priority', 1)}\n"
                f"📅 {ticket.get('create_date', 'N/A')}\n\n"
            )
        
        if len(message) > 4000:
            message = message[:4000] + "\n\n... (showing 10 most recent tickets)"
        
        return message
    
    @staticmethod
    def format_ticket_error(error_message: str) -> str:
        """Format ticket creation error message"""
        return (
            "❌ *Unable to create ticket.*\n\n"
            f"❗ *Error:* {error_message}\n\n"
            "Please try again later or contact admin for support."
        )