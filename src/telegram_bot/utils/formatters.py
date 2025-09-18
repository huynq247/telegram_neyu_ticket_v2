"""
Telegram Bot Formatters Module
Chứa các function format message và text
"""
from typing import Dict, Any, List

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
    def escape_markdown(text: str) -> str:
        """
        Escape special Markdown characters to prevent parsing errors
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text safe for Telegram Markdown
        """
        if not text:
            return ""
        
        # Characters that need escaping in Telegram Markdown
        special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = str(text)
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text
    
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
        """Format tickets list message using HTML formatting"""
        if not tickets:
            return (
                "📋 You don't have any tickets yet.\n"
                "Use /newticket to create a new ticket."
            )
        
        message = "📋 <b>Your tickets list:</b>\n\n"
        
        for ticket in tickets[-10:]:  # Show 10 most recent tickets
            status_emoji = BotFormatters.STATUS_EMOJIS.get(
                ticket.get('stage', 'new'), '❓'
            )
            priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
                ticket.get('priority', 1), '🟡'
            )
            
            # HTML escape ticket name
            ticket_name = str(ticket.get('name', 'Unknown'))
            ticket_name = ticket_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            message += (
                f"{status_emoji} <b>{ticket_name}</b>\n"
                f"🎫 <code>{ticket.get('ticket_number', 'N/A')}</code>\n"
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
    
    @staticmethod
    def format_ticket_detail(ticket: Dict[str, Any]) -> str:
        """
        Format single ticket detail view
        
        Args:
            ticket: Ticket data dictionary
            
        Returns:
            Formatted ticket detail message
        """
        if not ticket:
            return "❌ Ticket not found or error occurred."
        
        # Get status and priority emojis
        status_emoji = BotFormatters.STATUS_EMOJIS.get(
            ticket.get('stage_name', '').lower(), '❓'
        )
        priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
            ticket.get('priority', 1), '🟡'
        )
        
        # Format description with length limit and escape special characters
        description = ticket.get('description', 'No description')
        if len(description) > 200:
            description = description[:200] + "..."
        
        # Escape special characters to prevent Markdown parsing errors
        safe_title = BotFormatters.escape_markdown(str(ticket.get('name', 'Untitled')))
        safe_status = BotFormatters.escape_markdown(str(ticket.get('stage_name', 'Unknown')))
        safe_description = BotFormatters.escape_markdown(description)
        safe_create_date = BotFormatters.escape_markdown(str(ticket.get('create_date', 'N/A')))
        safe_write_date = BotFormatters.escape_markdown(str(ticket.get('write_date', 'N/A')))
        safe_tracking_id = BotFormatters.escape_markdown(str(ticket.get('tracking_id', 'N/A')))
        
        return (
            f"🎫 *Ticket Detail*\n\n"
            f"🔖 *ID:* `{ticket.get('id', 'N/A')}`\n"
            f"📋 *Title:* {safe_title}\n"
            f"{status_emoji} *Status:* {safe_status}\n"
            f"{priority_emoji} *Priority:* {ticket.get('priority', 1)}\n"
            f"📝 *Description:*\n{safe_description}\n\n"
            f"📅 *Created:* {safe_create_date}\n"
            f"🔄 *Updated:* {safe_write_date}\n"
            f"🔗 *Tracking:* `{safe_tracking_id}`"
        )
    
    @staticmethod
    def format_paginated_tickets(pagination_data: Dict[str, Any]) -> str:
        """
        Format paginated ticket list using HTML formatting
        
        Args:
            pagination_data: Dict with tickets, total_count, current_page, total_pages
            
        Returns:
            Formatted ticket list with pagination info
        """
        tickets = pagination_data.get('tickets', [])
        current_page = pagination_data.get('current_page', 1)
        total_pages = pagination_data.get('total_pages', 1)
        total_count = pagination_data.get('total_count', 0)
        
        if not tickets:
            return (
                "📋 <b>Your Tickets</b>\n\n"
                "🚫 No tickets found.\n"
                "Use /newticket to create your first ticket!"
            )
        
        message = f"📋 <b>Your Tickets</b> (Page {current_page}/{total_pages})\n"
        message += f"📊 Total: {total_count} tickets\n\n"
        
        for i, ticket in enumerate(tickets, 1):
            status_emoji = BotFormatters.STATUS_EMOJIS.get(
                ticket.get('stage_name', '').lower(), '❓'
            )
            priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
                ticket.get('priority', 1), '🟡'
            )
            
            # Limit title length - no need to escape for HTML
            title = ticket.get('name', 'Untitled')
            if len(title) > 30:
                title = title[:30] + "..."
            
            # HTML escape only special HTML characters
            title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            date_str = str(ticket.get('create_date', 'N/A'))
            
            message += (
                f"{i}. {status_emoji} <b>{title}</b>\n"
                f"   🎫 ID: <code>{ticket.get('id', 'N/A')}</code> {priority_emoji}\n"
                f"   📅 {date_str}\n"
                f"   ➡️ /detail_{ticket.get('id', 0)}\n\n"
            )
        
        if len(message) > 4000:
            message = message[:4000] + "\n\n... (truncated)"
        
        return message
    
    @staticmethod
    def format_filtered_tickets(tickets: List[Dict[str, Any]], filter_type: str, filter_value: str) -> str:
        """
        Format filtered ticket results
        
        Args:
            tickets: List of filtered tickets
            filter_type: Type of filter ('status' or 'priority')
            filter_value: Filter value
            
        Returns:
            Formatted filtered results
        """
        if not tickets:
            return (
                f"🔍 *Filter Results*\n\n"
                f"📌 Filter: {filter_type.title()} = {filter_value}\n"
                f"🚫 No tickets found matching this filter."
            )
        
        message = f"🔍 *Filtered Tickets*\n"
        message += f"📌 Filter: {filter_type.title()} = {filter_value}\n"
        message += f"📊 Found: {len(tickets)} tickets\n\n"
        
        for i, ticket in enumerate(tickets[:10], 1):  # Limit to 10 results
            status_emoji = BotFormatters.STATUS_EMOJIS.get(
                ticket.get('stage_name', '').lower(), '❓'
            )
            priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
                ticket.get('priority', 1), '🟡'
            )
            
            title = ticket.get('name', 'Untitled')
            if len(title) > 25:
                title = title[:25] + "..."
            
            # Escape special characters
            safe_title = BotFormatters.escape_markdown(title)
            safe_date = BotFormatters.escape_markdown(str(ticket.get('create_date', 'N/A')))
            
            message += (
                f"{i}. {status_emoji} *{safe_title}*\n"
                f"   🎫 ID: `{ticket.get('id', 'N/A')}` {priority_emoji}\n"
                f"   📅 {safe_date}\n\n"
            )
        
        if len(tickets) > 10:
            message += f"... and {len(tickets) - 10} more tickets"
        
        return message
    
    @staticmethod
    def format_search_results(tickets: List[Dict[str, Any]], search_term: str) -> str:
        """
        Format search results
        
        Args:
            tickets: List of tickets matching search
            search_term: Search term used
            
        Returns:
            Formatted search results
        """
        if not tickets:
            return (
                f"🔍 *Search Results*\n\n"
                f"🔎 Search term: \"{search_term}\"\n"
                f"🚫 No tickets found matching your search."
            )
        
        message = f"🔍 *Search Results*\n"
        message += f"🔎 Search term: \"{search_term}\"\n"
        message += f"📊 Found: {len(tickets)} tickets\n\n"
        
        for i, ticket in enumerate(tickets[:8], 1):  # Limit to 8 results for search
            status_emoji = BotFormatters.STATUS_EMOJIS.get(
                ticket.get('stage_name', '').lower(), '❓'
            )
            priority_emoji = BotFormatters.PRIORITY_EMOJIS.get(
                ticket.get('priority', 1), '🟡'
            )
            
            title = ticket.get('name', 'Untitled')
            if len(title) > 30:
                title = title[:30] + "..."
            
            message += (
                f"{i}. {status_emoji} *{title}*\n"
                f"   🎫 ID: `{ticket.get('id', 'N/A')}` {priority_emoji}\n"
                f"   📅 {ticket.get('create_date', 'N/A')}\n\n"
            )
        
        if len(tickets) > 8:
            message += f"... and {len(tickets) - 8} more results"
        
        return message