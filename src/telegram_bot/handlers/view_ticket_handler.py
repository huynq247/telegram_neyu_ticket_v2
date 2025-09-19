"""
View Ticket Handler Module
Xử lý tất cả các thao tác xem và quản lý tickets
"""
import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Conversation states
VIEWING_LIST, VIEWING_DETAIL, SEARCHING, FILTERING = range(4)

class ViewTicketHandler:
    """Handler cho việc xem và quản lý tickets"""
    
    # Make states accessible as class attributes
    VIEWING_LIST = VIEWING_LIST
    VIEWING_DETAIL = VIEWING_DETAIL
    SEARCHING = SEARCHING
    FILTERING = FILTERING
    
    def __init__(self, ticket_service, formatters, keyboards, auth_service):
        """
        Initialize ViewTicketHandler
        
        Args:
            ticket_service: Instance của TicketService
            formatters: Instance của BotFormatters
            keyboards: Instance của BotKeyboards
            auth_service: Instance của AuthService
        """
        self.ticket_service = ticket_service
        self.formatters = formatters
        self.keyboards = keyboards
        self.auth_service = auth_service
        
        # Store user states
        self.user_states = {}
    
    def _is_authenticated(self, user_id: int) -> bool:
        """Check if user is authenticated"""
        return self.auth_service.is_authenticated(user_id)
    
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
            
            # Get keyboard without detail buttons - only navigation
            keyboard = self._get_navigation_keyboard(
                current_page=pagination_data.get('current_page', 1),
                total_pages=pagination_data.get('total_pages', 1)
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
            
            return VIEWING_LIST
            
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
    
    async def handle_ticket_list_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle callback queries for ticket list navigation
        """
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        chat_id = str(query.message.chat_id)
        callback_data = query.data
        
        logger.info(f"handle_ticket_list_callback: user_id={user_id}, callback_data={callback_data}")
        
        try:
            if callback_data.startswith("view_page_"):
                if callback_data == "view_page_info":
                    # Page info button - do nothing, just answer the callback
                    return VIEWING_LIST
                else:
                    # Handle pagination
                    page = int(callback_data.split("_")[-1])
                    return await self._handle_pagination(query, chat_id, user_id, page)
            

            
            # REMOVED - Filter options no longer available
            # elif callback_data == "view_filter_status":
            #     # Show status filter options
            #     keyboard = self.keyboards.get_status_filter_keyboard()
            #     await query.edit_message_text(
            #         "🏷️ *Filter by Status*\n\nSelect status to filter your tickets:",
            #         reply_markup=keyboard,
            #         parse_mode='HTML'
            #     )
            #     return FILTERING
            # 
            # elif callback_data == "view_filter_priority":
            #     # Show priority filter options  
            #     keyboard = self.keyboards.get_priority_filter_keyboard()
            #     await query.edit_message_text(
            #         "⚡ *Filter by Priority*\n\nSelect priority level to filter your tickets:",
            #         reply_markup=keyboard,
            #         parse_mode='HTML'
            #     )
            #     return FILTERING
            
            elif callback_data == "view_search":
                # Start search process
                await query.edit_message_text(
                    "🔍 *Search Tickets*\n\nPlease enter search keywords:\n"
                    "• Search by ticket title\n"
                    "• Search by description content",
                    parse_mode='HTML'
                )
                return SEARCHING
            
            elif callback_data == "view_back_to_list":
                # Return to ticket list from search results
                logger.info(f"Processing view_back_to_list for user {user_id}")
                user_state = self._get_user_state(user_id)
                user_state['current_page'] = 1
                
                # Clear any search/filter state
                user_state.pop('search_term', None)
                user_state.pop('filter_type', None)
                user_state.pop('filter_value', None)
                
                # Get fresh ticket list
                pagination_data = await self.ticket_service.get_paginated_tickets(
                    user_id, self.auth_service, page=1, per_page=5
                )
                message = self.formatters.format_paginated_tickets(pagination_data)
                
                keyboard = self._get_navigation_keyboard(
                    current_page=pagination_data.get('current_page', 1),
                    total_pages=pagination_data.get('total_pages', 1)
                )
                
                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return VIEWING_LIST
            
            elif callback_data == "back_to_menu":
                # Return to main menu
                self._clear_user_state(user_id)
                keyboard = self.keyboards.get_main_menu_keyboard()
                await query.edit_message_text(
                    "🏠 *Main Menu*\n\nWhat would you like to do?",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return ConversationHandler.END
            
            else:
                return VIEWING_LIST
                
        except Exception as e:
            logger.error(f"Error handling ticket list callback: {e}")
            await query.edit_message_text("❌ Error occurred. Please try again.")
            return ConversationHandler.END
    
    async def _handle_pagination(self, query, chat_id: str, user_id: int, page: int) -> int:
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
            
            # Update keyboard - only navigation, no detail buttons
            keyboard = self._get_navigation_keyboard(
                current_page=pagination_data.get('current_page', page),
                total_pages=pagination_data.get('total_pages', 1)
            )
            
            # Update user state
            user_state['current_page'] = page
            user_state['last_tickets'] = pagination_data.get('tickets', [])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return VIEWING_LIST
            
        except Exception as e:
            logger.error(f"Error in pagination: {e}")
            await query.edit_message_text("❌ Error loading page.")
            return VIEWING_LIST
    
    async def _get_filtered_pagination(self, user_id: int, chat_id: str, page: int, status_filter: str, priority_filter: int) -> Dict[str, Any]:
        """Get filtered tickets with pagination simulation"""
        try:
            # Get filtered tickets (all)
            filtered_tickets = await self.ticket_service.get_filtered_tickets(
                user_id, self.auth_service, status_filter, priority_filter
            )
            
            # Simulate pagination
            per_page = 5
            total_count = len(filtered_tickets)
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            page_tickets = filtered_tickets[start_idx:end_idx]
            
            return {
                'tickets': page_tickets,
                'total_count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'per_page': per_page
            }
            
        except Exception as e:
            logger.error(f"Error in filtered pagination: {e}")
            return {
                'tickets': [],
                'total_count': 0,
                'current_page': 1,
                'total_pages': 0,
                'per_page': 5
            }
    
    # REMOVED - Filter functionality no longer needed
    # async def handle_filter_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     """
    #     Handle filter selection callbacks
    #     """
    #     query = update.callback_query
    #     await query.answer()
    #     
    #     user_id = query.from_user.id
    #     chat_id = str(query.message.chat_id)
    #     callback_data = query.data
    #     
    #     try:
    #         user_state = self._get_user_state(user_id)
    #         
    #         if callback_data.startswith("filter_status_"):
    #             filter_value = callback_data.split("_")[-1]
    #             
    #             if filter_value == "all":
    #                 # Clear status filter
    #                 user_state['filter_type'] = None
    #                 user_state['filter_value'] = None
    #                 tickets = await self.ticket_service.get_user_tickets(user_id, self.auth_service)
    #                 message = self.formatters.format_tickets_list(tickets)
    #             else:
    #                 # Apply status filter
    #                 user_state['filter_type'] = 'status'
    #                 user_state['filter_value'] = filter_value
    #                 tickets = await self.ticket_service.get_filtered_tickets(
    #                     user_id, self.auth_service, status_filter=filter_value
    #                 )
    #                 message = self.formatters.format_filtered_tickets(
    #                     tickets, 'status', filter_value.replace('_', ' ').title()
    #                 )
    #         
    #         elif callback_data.startswith("filter_priority_"):
    #             filter_value = callback_data.split("_")[-1]
    #             
    #             if filter_value == "all":
    #                 # Clear priority filter
    #                 user_state['filter_type'] = None
    #                 user_state['filter_value'] = None
    #                 tickets = await self.ticket_service.get_user_tickets(user_id, self.auth_service)
    #                 message = self.formatters.format_tickets_list(tickets)
    #             else:
    #                 # Apply priority filter
    #                 priority_int = int(filter_value)
    #                 user_state['filter_type'] = 'priority'
    #                 user_state['filter_value'] = priority_int
    #                 tickets = await self.ticket_service.get_filtered_tickets(
    #                     user_id, self.auth_service, priority_filter=priority_int
    #                 )
    #                 priority_names = {1: 'Low', 2: 'Normal', 3: 'High', 4: 'Urgent'}
    #                 message = self.formatters.format_filtered_tickets(
    #                     tickets, 'priority', priority_names.get(priority_int, str(priority_int))
    #                 )
    #         
    #         elif callback_data == "view_back_to_list":
    #             # Return to ticket list
    #             user_state['current_page'] = 1
    #             pagination_data = await self.ticket_service.get_paginated_tickets(user_id, self.auth_service, page=1, per_page=5)
    #             message = self.formatters.format_paginated_tickets(pagination_data)
    #             
    #             keyboard = self._get_navigation_keyboard(
    #                 current_page=pagination_data.get('current_page', 1),
    #                 total_pages=pagination_data.get('total_pages', 1)
    #             )
    #             
    #             await query.edit_message_text(
    #                 message,
    #                 reply_markup=keyboard,
    #                 parse_mode='HTML'
    #             )
    #             return VIEWING_LIST
    #         
    #         # Update message with filter results
    #         keyboard = self._get_navigation_keyboard(
    #             current_page=1,
    #             total_pages=1
    #         )
    #         
    #         await query.edit_message_text(
    #             message,
    #             reply_markup=keyboard,
    #             parse_mode='HTML'
    #         )
    #         
    #         return VIEWING_LIST
    #         
    #     except Exception as e:
    #         logger.error(f"Error handling filter callback: {e}")
    #         await query.edit_message_text("❌ Error applying filter.")
    #         return FILTERING
    
    async def handle_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle search input from user
        """
        user_id = update.effective_user.id
        chat_id = str(update.effective_chat.id)
        search_term = update.message.text.strip()
        
        if len(search_term) < 2:
            await update.message.reply_text(
                "❌ Search term must be at least 2 characters long. Please try again:"
            )
            return SEARCHING
        
        try:
            # Search tickets
            tickets = await self.ticket_service.search_tickets(user_id, self.auth_service, search_term)
            
            # Format results
            message = self.formatters.format_search_results(tickets, search_term)
            
            # Get keyboard
            keyboard = self.keyboards.get_search_result_keyboard(
                current_page=1,
                total_pages=1
            )
            
            # Update user state
            user_state = self._get_user_state(user_id)
            user_state['search_term'] = search_term
            user_state['last_tickets'] = tickets
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return VIEWING_LIST
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            await update.message.reply_text("❌ Error occurred during search.")
            return SEARCHING
    
    async def handle_ticket_detail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """
        Handle /detail_<ticket_id> command
        """
        user_id = update.effective_user.id
        command_text = update.message.text
        
        logger.info(f"handle_ticket_detail_command: user_id={user_id}, command={command_text}")
        
        # Check authentication
        if not self._is_authenticated(user_id):
            await update.message.reply_text(
                "🔒 You need to login first. Use /login to authenticate."
            )
            return ConversationHandler.END
        
        try:
            # Extract ticket ID from command
            command_text = update.message.text
            if not command_text.startswith('/detail_'):
                await update.message.reply_text("❌ Invalid command format.")
                return ConversationHandler.END
            
            ticket_id = int(command_text.split('_')[1])
            
            # Get ticket detail
            ticket = await self.ticket_service.get_ticket_detail(ticket_id)
            
            if not ticket:
                await update.message.reply_text("❌ Ticket not found or access denied.")
                return ConversationHandler.END
            
            # Format detail message
            message = self.formatters.format_ticket_detail(ticket)
            
            # Get detail keyboard
            keyboard = self.keyboards.get_ticket_detail_keyboard(ticket_id)
            
            await update.message.reply_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return VIEWING_DETAIL
            
        except ValueError:
            await update.message.reply_text("❌ Invalid ticket ID.")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error showing ticket detail: {e}")
            await update.message.reply_text("❌ Error loading ticket detail.")
            return ConversationHandler.END
    
    async def _send_tickets_individually(self, update: Update, pagination_data: Dict[str, Any]) -> None:
        """Send each ticket as individual message with its detail button"""
        tickets = pagination_data.get('tickets', [])
        current_page = pagination_data.get('current_page', 1)
        total_pages = pagination_data.get('total_pages', 1)
        total_count = pagination_data.get('total_count', 0)
        
        # Send header message first
        header_message = f"📋 <b>Your Tickets</b> (Page {current_page}/{total_pages})\n📊 Total: {total_count} tickets\n"
        
        if not tickets:
            header_message += "\n🚫 No tickets found.\nUse /newticket to create your first ticket!"
            
            # Send header with navigation only
            nav_keyboard = self._get_navigation_keyboard(current_page, total_pages)
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    header_message,
                    reply_markup=nav_keyboard,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    header_message,
                    reply_markup=nav_keyboard,
                    parse_mode='HTML'
                )
            return
        
        # Send header
        if update.callback_query:
            # Edit the existing message to header
            await update.callback_query.edit_message_text(
                header_message,
                parse_mode='HTML'
            )
            
            # Send individual tickets
            for i, ticket in enumerate(tickets, 1):
                ticket_message = self.formatters.format_single_ticket(ticket, i)
                
                # Create detail button for this ticket
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"📄 View Detail", callback_data=f"view_detail_{ticket.get('id')}")
                ]])
                
                await update.callback_query.message.reply_text(
                    ticket_message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            
            # Send navigation controls at the end
            nav_keyboard = self._get_navigation_keyboard(current_page, total_pages)
            await update.callback_query.message.reply_text(
                "🎛️ <b>Navigation & Actions</b>",
                reply_markup=nav_keyboard,
                parse_mode='HTML'
            )
        else:
            # Send header
            await update.message.reply_text(
                header_message,
                parse_mode='HTML'
            )
            
            # Send individual tickets
            for i, ticket in enumerate(tickets, 1):
                ticket_message = self.formatters.format_single_ticket(ticket, i)
                
                # Create detail button for this ticket
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(f"📄 View Detail", callback_data=f"view_detail_{ticket.get('id')}")
                ]])
                
                await update.message.reply_text(
                    ticket_message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            
            # Send navigation controls at the end
            nav_keyboard = self._get_navigation_keyboard(current_page, total_pages)
            await update.message.reply_text(
                "🎛️ <b>Navigation & Actions</b>",
                reply_markup=nav_keyboard,
                parse_mode='HTML'
            )
    
    async def _send_tickets_with_individual_details(self, update: Update, pagination_data: Dict[str, Any]) -> None:
        """Send tickets as individual messages with detail buttons"""
        tickets = pagination_data.get('tickets', [])
        current_page = pagination_data.get('current_page', 1)
        total_pages = pagination_data.get('total_pages', 1)
        total_count = pagination_data.get('total_count', 0)
        
        # First send header message
        header_message = f"📋 <b>Your Tickets</b> (Page {current_page}/{total_pages})\n📊 Total: {total_count} tickets\n"
        
        if not tickets:
            header_message += "\n🚫 No tickets found.\nUse /newticket to create your first ticket!"
            
        # Send header
        if update.callback_query:
            await update.callback_query.edit_message_text(
                header_message,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                header_message,
                parse_mode='HTML'
            )
        
        # Send each ticket with its detail button
        for i, ticket in enumerate(tickets, 1):
            ticket_message = self.formatters.format_single_ticket(ticket, i)
            
            # Create individual detail button
            keyboard = [[
                InlineKeyboardButton(f"📄 View Detail", callback_data=f"view_detail_{ticket.get('id')}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send ticket message
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    ticket_message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    ticket_message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        
        # Send navigation controls
        if total_pages > 1 or tickets:
            nav_keyboard = self._get_navigation_keyboard(current_page, total_pages)
            nav_message = "🎛️ <b>Navigation & Actions</b>"
            
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    nav_message,
                    reply_markup=nav_keyboard,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    nav_message,
                    reply_markup=nav_keyboard,
                    parse_mode='HTML'
                )
    
    def _get_navigation_keyboard(self, current_page: int, total_pages: int):
        """Get navigation keyboard without detail buttons"""
        keyboard = []
        
        # Search option only
        keyboard.append([
            InlineKeyboardButton("🔍 Search", callback_data="view_search")
        ])
        
        # Pagination
        if total_pages > 1:
            pagination_row = []
            if current_page > 1:
                pagination_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"view_page_{current_page-1}"))
            
            pagination_row.append(InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="view_page_info"))
            
            if current_page < total_pages:
                pagination_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"view_page_{current_page+1}"))
            
            keyboard.append(pagination_row)
        
        # Back to main menu
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _handle_ticket_detail_view(self, query, user_id: int, ticket_id: int) -> int:
        """Handle ticket detail view from callback"""
        try:
            # Get ticket detail
            ticket = await self.ticket_service.get_ticket_detail(ticket_id)
            
            if not ticket:
                await query.edit_message_text("❌ Ticket not found or access denied.")
                return ConversationHandler.END
            
            # Format detail message
            message = self.formatters.format_ticket_detail(ticket)
            
            # Get detail keyboard
            keyboard = self.keyboards.get_ticket_detail_keyboard(ticket_id)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return VIEWING_DETAIL
            
        except Exception as e:
            logger.error(f"Error showing ticket detail: {e}")
            await query.edit_message_text("❌ Error loading ticket detail.")
            return ConversationHandler.END

    async def cancel_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel view ticket conversation"""
        user_id = update.effective_user.id
        self._clear_user_state(user_id)
        
        await update.message.reply_text(
            "🚫 View ticket cancelled. Use /mytickets to view your tickets again."
        )
        return ConversationHandler.END
