"""
Ticket List Handler Module
Xử lý các thao tác liên quan đến danh sách tickets, pagination, và search
"""
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .base_view_handler import BaseViewHandler, SEARCHING

logger = logging.getLogger(__name__)

class TicketListHandler(BaseViewHandler):
    """Handler for ticket list operations"""
    
    async def view_tickets_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Command handler để xem danh sách tickets
        """
        user_id = update.effective_user.id
        
        # Check authentication
        if not self._is_authenticated(user_id):
            message_text = "🔒 You need to login first. Use /login to authenticate."
            
            # Handle both callback query and message
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    message_text,
                    parse_mode='HTML'
                )
            return ConversationHandler.END
        
        try:
            logger.info(f"Loading tickets for user_id: {user_id}")
            
            # Get paginated tickets using user_id and auth_service
            pagination_data = await self.ticket_service.get_paginated_tickets(user_id, self.auth_service, page=1, per_page=5)
            logger.info(f"Pagination data: {pagination_data}")
            
            # Format message
            message = self.formatters.format_paginated_tickets(pagination_data)
            logger.info(f"Formatted message length: {len(message)}")
            
            # Get keyboard with comment buttons
            keyboard = self.keyboards.get_ticket_list_keyboard(
                current_page=pagination_data.get('current_page', 1),
                total_pages=pagination_data.get('total_pages', 1),
                has_tickets=len(pagination_data.get('tickets', [])) > 0,
                tickets=pagination_data.get('tickets', [])
            )
            
            # Update user state
            user_state = self._get_user_state(user_id)
            user_state['current_page'] = 1
            user_state['last_tickets'] = pagination_data.get('tickets', [])
            
            # Handle both callback query and message - using HTML to avoid Markdown parsing issues
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            
            return self.VIEWING_LIST
            
        except Exception as e:
            logger.error(f"Error in view_tickets_command: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            error_message = "❌ Error occurred while loading tickets."
            
            # Handle both callback query and message
            if update.callback_query:
                await update.callback_query.edit_message_text(error_message)
            else:
                await update.message.reply_text(error_message)
            return ConversationHandler.END
    
    async def handle_pagination(self, query, chat_id: str, user_id: int, page: int) -> int:
        """Handle pagination logic"""
        try:
            logger.info(f"_handle_pagination called: user_id={user_id}, page={page}")
            user_state = self._get_user_state(user_id)
            
            # Get tickets for the requested page
            if user_state.get('filter_type'):
                # Apply current filter
                logger.info(f"Using filter: {user_state['filter_type']} = {user_state['filter_value']}")
                if user_state['filter_type'] == 'status':
                    pagination_data = await self._get_filtered_pagination(
                        user_id, chat_id, page, user_state['filter_value'], None
                    )
                else:  # priority
                    pagination_data = await self._get_filtered_pagination(
                        user_id, chat_id, page, None, user_state['filter_value']
                    )
            else:
                # Regular pagination
                logger.info(f"Getting regular pagination for page {page}")
                pagination_data = await self.ticket_service.get_paginated_tickets(
                    user_id, self.auth_service, page=page, per_page=5
                )
                logger.info(f"Got pagination data: {pagination_data.get('current_page', 'N/A')}/{pagination_data.get('total_pages', 'N/A')}")
            
            # Format message
            message = self.formatters.format_paginated_tickets(pagination_data)
            
            # Update keyboard with comment buttons
            keyboard = self.keyboards.get_ticket_list_keyboard(
                current_page=pagination_data.get('current_page', page),
                total_pages=pagination_data.get('total_pages', 1),
                has_tickets=len(pagination_data.get('tickets', [])) > 0,
                tickets=pagination_data.get('tickets', [])
            )
            
            # Update user state
            user_state['current_page'] = page
            user_state['last_tickets'] = pagination_data.get('tickets', [])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return self.VIEWING_LIST
            
        except Exception as e:
            logger.error(f"Error in pagination: {e}")
            await query.edit_message_text("❌ Error loading page.")
            return self.VIEWING_LIST
    
    async def handle_search_tickets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle search tickets button click"""
        query = update.callback_query
        
        # Start search process
        await query.edit_message_text(
            "🔍 *Search Tickets*\n\nPlease enter search keywords:\n"
            "• Search by ticket title\n"
            "• Search by description content",
            parse_mode='HTML'
        )
        return SEARCHING
    
    async def handle_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle search input from user"""
        user_id = update.message.from_user.id
        search_term = update.message.text.strip()
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return ConversationHandler.END
        
        try:
            logger.info(f"Searching tickets for user {user_id} with term: {search_term}")
            
            # Perform search
            search_results = await self.ticket_service.search_tickets(
                user_id, self.auth_service, search_term
            )
            
            if not search_results:
                await update.message.reply_text(
                    f"🔍 No tickets found for: '{search_term}'\\n\\n"
                    "Try different keywords or check your spelling.",
                    reply_markup=self.keyboards.get_back_to_tickets_keyboard(),
                    parse_mode='HTML'
                )
                return self.VIEWING_LIST
            
            # Format search results as pagination data
            pagination_data = {
                'tickets': search_results,
                'current_page': 1,
                'total_pages': 1,
                'total_tickets': len(search_results),
                'per_page': len(search_results)
            }
            
            # Update user state with search
            user_state = self._get_user_state(user_id)
            user_state['search_term'] = search_term
            user_state['current_page'] = 1
            user_state['last_tickets'] = search_results
            
            # Format message
            message = f"🔍 Search Results for: '{search_term}'\\n\\n"
            message += self.formatters.format_paginated_tickets(pagination_data)
            
            # Get keyboard
            keyboard = self.keyboards.get_ticket_list_keyboard(
                current_page=1,
                total_pages=1,
                has_tickets=True,
                tickets=search_results
            )
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return self.VIEWING_LIST
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            await update.message.reply_text(
                "❌ Error occurred during search. Please try again.",
                reply_markup=self.keyboards.get_back_to_tickets_keyboard()
            )
            return self.VIEWING_LIST
    
    async def handle_ticket_detail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ticket detail command like /detail_123"""
        user_id = update.message.from_user.id
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return ConversationHandler.END
        
        # Extract ticket ID from command
        command_text = update.message.text
        try:
            ticket_id = int(command_text.split('_')[1])
            logger.info(f"User {user_id} viewing ticket detail for ID: {ticket_id}")
            
            return await self._handle_ticket_detail_view(update.message, user_id, ticket_id)
            
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid ticket detail command format: {command_text}, error: {e}")
            await update.message.reply_text(
                "❌ Invalid command format. Use /detail_<ticket_number>",
                reply_markup=self.keyboards.get_back_to_tickets_keyboard()
            )
            return self.VIEWING_LIST
    
    async def _get_filtered_pagination(self, user_id: int, chat_id: str, page: int, status_filter: str, priority_filter: int) -> Dict[str, Any]:
        """Get filtered tickets with pagination simulation"""
        try:
            # Get filtered tickets (all)
            filtered_tickets = await self.ticket_service.get_filtered_tickets(
                user_id, self.auth_service, status_filter, priority_filter
            )
            
            # Simulate pagination on filtered results
            per_page = 5
            total_tickets = len(filtered_tickets)
            total_pages = max(1, (total_tickets + per_page - 1) // per_page)
            
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            page_tickets = filtered_tickets[start_index:end_index]
            
            return {
                'tickets': page_tickets,
                'current_page': page,
                'total_pages': total_pages,
                'total_tickets': total_tickets,
                'per_page': per_page
            }
            
        except Exception as e:
            logger.error(f"Error in filtered pagination: {e}")
            return {
                'tickets': [],
                'current_page': 1,
                'total_pages': 1,
                'total_tickets': 0,
                'per_page': 5
            }
    
    async def _handle_ticket_detail_view(self, message_or_query, user_id: int, ticket_id: int) -> int:
        """Handle ticket detail view"""
        try:
            # Get ticket details
            ticket_details = await self.ticket_service.get_ticket_details(
                user_id, self.auth_service, ticket_id
            )
            
            if not ticket_details:
                error_text = f"❌ Ticket #{ticket_id} not found or you don't have access to it."
                keyboard = self.keyboards.get_back_to_tickets_keyboard()
                
                if hasattr(message_or_query, 'edit_message_text'):
                    await message_or_query.edit_message_text(error_text, reply_markup=keyboard)
                else:
                    await message_or_query.reply_text(error_text, reply_markup=keyboard)
                
                return self.VIEWING_LIST
            
            # Format ticket details
            message = self.formatters.format_ticket_details(ticket_details)
            keyboard = self.keyboards.get_ticket_detail_keyboard(ticket_id)
            
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(
                    message, 
                    reply_markup=keyboard, 
                    parse_mode='HTML'
                )
            else:
                await message_or_query.reply_text(
                    message, 
                    reply_markup=keyboard, 
                    parse_mode='HTML'
                )
            
            return self.VIEWING_DETAIL
            
        except Exception as e:
            logger.error(f"Error viewing ticket {ticket_id}: {e}")
            error_text = "❌ Error loading ticket details."
            keyboard = self.keyboards.get_back_to_tickets_keyboard()
            
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(error_text, reply_markup=keyboard)
            else:
                await message_or_query.reply_text(error_text, reply_markup=keyboard)
            
            return self.VIEWING_LIST