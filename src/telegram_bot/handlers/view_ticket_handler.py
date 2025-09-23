"""
View Ticket Handler Module - Main Orchestrator

This is the main entry point for all ticket-related operations.
It coordinates between specialized handlers for different functionalities:
- TicketListHandler: Main ticket viewing and pagination
- TicketCommentHandler: Comment viewing and adding  
- AwaitingTicketsHandler: Awaiting tickets operations
"""

import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Import specialized handlers
from .view_ticket.base_view_handler import BaseViewHandler
from .view_ticket.ticket_list_handler import TicketListHandler
from .view_ticket.ticket_comment_handler import TicketCommentHandler
from .view_ticket.awaiting_tickets_handler import AwaitingTicketsHandler

# Import states from base handler
from .view_ticket.base_view_handler import (
    VIEWING_LIST, VIEWING_DETAIL, SEARCHING, FILTERING, VIEWING_COMMENTS, 
    WAITING_TICKET_NUMBER, WAITING_ADD_COMMENT_TICKET, WAITING_COMMENT_TEXT, 
    VIEWING_AWAITING, WAITING_AWAITING_COMMENT
)

logger = logging.getLogger(__name__)


class ViewTicketHandler(BaseViewHandler):
    """Main orchestrator for all ticket-related operations"""
    
    # Make states accessible as class attributes for backward compatibility
    VIEWING_LIST = VIEWING_LIST
    VIEWING_DETAIL = VIEWING_DETAIL
    SEARCHING = SEARCHING
    FILTERING = FILTERING
    VIEWING_COMMENTS = VIEWING_COMMENTS
    WAITING_TICKET_NUMBER = WAITING_TICKET_NUMBER
    WAITING_ADD_COMMENT_TICKET = WAITING_ADD_COMMENT_TICKET
    WAITING_COMMENT_TEXT = WAITING_COMMENT_TEXT
    VIEWING_AWAITING = VIEWING_AWAITING
    WAITING_AWAITING_COMMENT = WAITING_AWAITING_COMMENT
    
    def __init__(self, ticket_service, formatters, keyboards, auth_service):
        """
        Initialize ViewTicketHandler with specialized handlers
        
        Args:
            ticket_service: Instance của TicketService
            formatters: Instance của BotFormatters
            keyboards: Instance của BotKeyboards
            auth_service: Instance của AuthService
        """
        super().__init__(ticket_service, auth_service, formatters, keyboards)
        
        # Initialize specialized handlers
        self.ticket_list_handler = TicketListHandler(ticket_service, auth_service, formatters, keyboards)
        self.comment_handler = TicketCommentHandler(ticket_service, auth_service)
        self.awaiting_handler = AwaitingTicketsHandler(ticket_service, auth_service, keyboards)
        
        # Store user states
        self.user_states = {}
    
    def _get_user_state(self, user_id: int) -> Dict[str, Any]:
        """Get user state data"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                'current_page': 1,
                'filter_type': None,
                'filter_value': None,
                'search_term': None,
                'last_tickets': []
            }
        return self.user_states[user_id]
    
    def _clear_user_state(self, user_id: int):
        """Clear user state data"""
        if user_id in self.user_states:
            del self.user_states[user_id]

    # Main entry points - delegate to specialized handlers
    async def view_tickets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Main command handler - delegates to ticket list handler"""
        return await self.ticket_list_handler.view_tickets_command(update, context)

    async def handle_pagination(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle pagination - delegates to ticket list handler"""
        return await self.ticket_list_handler.handle_pagination(update, context)

    async def handle_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle search input - delegates to ticket list handler"""
        return await self.ticket_list_handler.handle_search_input(update, context)

    async def ticket_detail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ticket detail - delegates to ticket list handler"""
        return await self.ticket_list_handler.ticket_detail_command(update, context)

    async def handle_ticket_detail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ticket detail command - alias for backward compatibility"""
        return await self.ticket_detail_command(update, context)

    # Comment-related operations - delegate to comment handler
    async def handle_view_comments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle view comments - delegates to comment handler"""
        return await self.comment_handler.handle_view_comments(update, context)

    async def handle_ticket_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ticket number input - delegates to comment handler"""
        return await self.comment_handler.handle_ticket_number_input(update, context)

    async def handle_add_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle add comment - delegates to comment handler"""
        return await self.comment_handler.handle_add_comment(update, context)

    async def handle_add_comment_ticket_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle add comment ticket input - delegates to comment handler"""
        return await self.comment_handler.handle_add_comment_ticket_input(update, context)

    async def handle_comment_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle comment text input - delegates to comment handler"""
        return await self.comment_handler.handle_comment_text_input(update, context)

    # Awaiting tickets operations - delegate to awaiting handler
    async def handle_awaiting_tickets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle awaiting tickets - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_awaiting_tickets(update, context)

    async def handle_awaiting_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle awaiting comment - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_awaiting_comment(update, context)

    async def handle_awaiting_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle awaiting done - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_awaiting_done(update, context)

    async def handle_awaiting_comment_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle awaiting comment input - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_awaiting_comment_input(update, context)

    async def handle_awaiting_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle awaiting info - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_awaiting_info(update, context)

    async def handle_separator(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle separator - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_separator(update, context)

    # Deep link command handlers
    async def handle_addcomment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /addcomment command - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_addcomment_command(update, context)

    async def handle_markdone_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /markdone command - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_markdone_command(update, context)

    async def handle_global_comment_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle global comment input - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_global_comment_input(update, context)

    async def handle_addcomment_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ticket_number: str) -> None:
        """Handle add comment direct - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_addcomment_direct(update, context, ticket_number)

    async def handle_markdone_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ticket_number: str) -> None:
        """Handle mark done direct - delegates to awaiting handler"""
        return await self.awaiting_handler.handle_markdone_direct(update, context, ticket_number)

    # Main callback handler - routes to appropriate specialized handler
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Main callback handler that routes to appropriate specialized handlers
        """
        query = update.callback_query
        callback_data = query.data
        user_id = query.from_user.id
        
        logger.info(f"ViewTicket callback: {callback_data}, user_id: {user_id}")
        
        try:
            # Route based on callback data to appropriate handler
            if callback_data.startswith("view_page_") and callback_data != "view_page_info":
                await query.answer()
                # Handle pagination
                page = int(callback_data.split("_")[-1])
                chat_id = str(query.message.chat_id)
                return await self.ticket_list_handler.handle_pagination(query, chat_id, user_id, page)
            
            elif callback_data.startswith("detail_"):
                await query.answer()
                return await self.ticket_list_handler.ticket_detail_command(update, context)
            
            elif callback_data == "search_tickets" or callback_data == "view_search":
                await query.answer()
                return await self.ticket_list_handler.handle_search_tickets(update, context)
            
            elif callback_data == "back_to_tickets" or callback_data == "view_back_to_list":
                await query.answer()
                return await self.ticket_list_handler.view_tickets_command(update, context)
            
            elif callback_data == "view_page_info":
                # Just answer the callback for page info (non-interactive)
                await query.answer(f"Current page information")
                return VIEWING_LIST
            
            elif callback_data == "back_to_menu":
                # End conversation and return to menu
                await query.answer("Returning to main menu")
                logger.info(f"Ending conversation for user {user_id}, returning to main menu")
                
                # Get main menu keyboard and show it
                from ..utils.keyboards import BotKeyboards
                keyboards = BotKeyboards()
                main_menu_keyboard = keyboards.get_main_menu_keyboard()
                
                await query.edit_message_text(
                    "🏠 Main Menu - Choose an option:",
                    reply_markup=main_menu_keyboard
                )
                
                return ConversationHandler.END
            
            elif callback_data == "view_comments":
                await query.answer()
                return await self.comment_handler.handle_view_comments(update, context)
            
            elif callback_data == "add_comment":
                await query.answer()
                return await self.comment_handler.handle_add_comment(update, context)
            
            elif callback_data == "back_to_comments":
                await query.answer()
                return await self.comment_handler.handle_back_to_comments(update, context)
            
            elif callback_data == "view_awaiting":
                await query.answer()
                return await self.awaiting_handler.handle_awaiting_tickets(update, context)
            
            elif callback_data.startswith("awaiting_done_"):
                await query.answer()
                return await self.awaiting_handler.handle_awaiting_done(update, context)
            
            elif callback_data.startswith("awaiting_comment_"):
                await query.answer()
                return await self.awaiting_handler.handle_awaiting_comment(update, context)
            
            elif callback_data.startswith("awaiting_info_"):
                # Let the handler answer with specific message
                return await self.awaiting_handler.handle_awaiting_info(update, context)
            
            elif callback_data == "separator":
                await query.answer()
                return await self.awaiting_handler.handle_separator(update, context)
            
            else:
                logger.warning(f"Unknown callback data: {callback_data}")
                await query.answer("Unknown action")
                return VIEWING_LIST
                
        except Exception as e:
            logger.error(f"Error handling callback {callback_data}: {e}")
            await query.answer("Error processing request")
            return VIEWING_LIST