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
VIEWING_LIST, VIEWING_DETAIL, SEARCHING, FILTERING, VIEWING_COMMENTS, WAITING_TICKET_NUMBER, WAITING_ADD_COMMENT_TICKET, WAITING_COMMENT_TEXT, VIEWING_AWAITING, WAITING_AWAITING_COMMENT = range(10)

class ViewTicketHandler:
    """Handler cho việc xem và quản lý tickets"""
    
    # Make states accessible as class attributes
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
            
            elif callback_data.startswith("awaiting_done_"):
                # Handle mark done from awaiting tickets detailed button
                ticket_number = callback_data.replace("awaiting_done_", "")
                return await self.handle_markdone_direct(update, context, ticket_number)
            
            elif callback_data.startswith("awaiting_comment_"):
                # Handle add comment from awaiting tickets detailed button  
                ticket_number = callback_data.replace("awaiting_comment_", "")
                return await self.handle_addcomment_direct(update, context, ticket_number)
            
            elif callback_data == "spacer":
                # Handle spacer button - just ignore
                await query.answer()
                return self.VIEWING_AWAITING
            
            elif callback_data == "comment_instruction":
                # Handle comment instruction button - just ignore
                await query.answer()
                return self.VIEWING_AWAITING
            
            elif callback_data == "view_awaiting":
                # Handle back to awaiting tickets from comment screen
                return await self.handle_awaiting_tickets(update, context)
            
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
                
                keyboard = self.keyboards.get_ticket_list_keyboard(
                    current_page=pagination_data.get('current_page', 1),
                    total_pages=pagination_data.get('total_pages', 1),
                    has_tickets=len(pagination_data.get('tickets', [])) > 0,
                    tickets=pagination_data.get('tickets', [])
                )
                
                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return VIEWING_LIST
            
            elif callback_data == "back_to_tickets":
                # Return to tickets list from comments view
                logger.info(f"Processing back_to_tickets for user {user_id}")
                user_state = self._get_user_state(user_id)
                user_state['current_page'] = 1
                
                # Clear current ticket number from context
                context.user_data.pop('current_ticket_number', None)
                
                # Get fresh ticket list
                pagination_data = await self.ticket_service.get_paginated_tickets(
                    user_id, self.auth_service, page=1, per_page=5
                )
                message = self.formatters.format_paginated_tickets(pagination_data)
                
                keyboard = self.keyboards.get_ticket_list_keyboard(
                    current_page=pagination_data.get('current_page', 1),
                    total_pages=pagination_data.get('total_pages', 1),
                    has_tickets=len(pagination_data.get('tickets', [])) > 0,
                    tickets=pagination_data.get('tickets', [])
                )
                
                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return VIEWING_LIST
            
            elif callback_data == "back_to_comments":
                # Return to comments view from add comment
                logger.info(f"Processing back_to_comments for user {user_id}")
                current_ticket_number = context.user_data.get('current_ticket_number')
                
                if current_ticket_number:
                    # Get comments again
                    comments = await self._get_ticket_comments(current_ticket_number)
                    message = self._format_comments_display(current_ticket_number, comments)
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=self._get_comments_keyboard(),
                        parse_mode='HTML'
                    )
                    return VIEWING_COMMENTS
                else:
                    # If no current ticket, return to tickets list
                    pagination_data = await self.ticket_service.get_paginated_tickets(
                        user_id, self.auth_service, page=1, per_page=5
                    )
                    message = self.formatters.format_paginated_tickets(pagination_data)
                
                keyboard = self.keyboards.get_ticket_list_keyboard(
                    current_page=pagination_data.get('current_page', 1),
                    total_pages=pagination_data.get('total_pages', 1),
                    has_tickets=len(pagination_data.get('tickets', [])) > 0,
                    tickets=pagination_data.get('tickets', [])
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

    async def handle_view_comments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle view comments button click"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        logger.info(f"handle_view_comments: user_id={user_id}")
        
        # Check authentication
        if not self._is_authenticated(user_id):
            await query.edit_message_text(
                "🔒 You need to login first. Use /login to authenticate."
            )
            return ConversationHandler.END
        
        try:
            # Get recent tickets for reference
            recent_tickets = await self.ticket_service.get_recent_tickets(user_id, self.auth_service, limit=10)
            logger.info(f"Got {len(recent_tickets)} recent tickets for user {user_id}")
            
            # Format message with recent tickets list
            message = "🎫 **View Comments - Select a Ticket**\n\n"
            message += "📋 **Recent Tickets:**\n"
            
            if recent_tickets:
                for i, ticket in enumerate(recent_tickets, 1):
                    ticket_number = ticket.get('tracking_id', 'N/A')
                    status = ticket.get('stage_name', 'Unknown')
                    create_date = ticket.get('create_date', 'Unknown')
                    
                    # Format date
                    if create_date != 'Unknown':
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(create_date, '%Y-%m-%d %H:%M')
                            formatted_date = date_obj.strftime('%m/%d %H:%M')
                        except:
                            formatted_date = create_date
                    else:
                        formatted_date = 'Unknown'
                    
                    message += f"{i}. `{ticket_number}` - {status} - {formatted_date}\n"
                
                message += "\n💬 **Enter ticket number to view comments:**\n"
                message += "Example: TH220925757, VN00027, IN00602"
            else:
                message += "No recent tickets found.\n\n"
                message += "💬 **Enter ticket number to view comments:**"
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error getting recent tickets: {e}")
            # Fallback to simple message
            await query.edit_message_text(
                "🎫 Please enter the ticket number to view comments:\n\n"
                "Example: TH220925757, VN00027, IN00602",
                parse_mode='HTML'
            )
        
        return WAITING_TICKET_NUMBER

    async def handle_ticket_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ticket number input for viewing comments"""
        user_id = update.effective_user.id
        ticket_number = update.message.text.strip()
        
        logger.info(f"handle_ticket_number_input: user_id={user_id}, ticket_number={ticket_number}")
        
        # Check authentication
        if not self._is_authenticated(user_id):
            await update.message.reply_text(
                "🔒 You need to login first. Use /login to authenticate."
            )
            return ConversationHandler.END
        
        # Validate ticket number format
        is_valid = self._is_valid_ticket_number(ticket_number)
        logger.info(f"Validation result for '{ticket_number}': {is_valid}")
        
        if not is_valid:
            keyboard = [
                [
                    InlineKeyboardButton("⬅️ Back to My Tickets", callback_data="back_to_tickets"),
                    InlineKeyboardButton("✍️ Add Comment", callback_data="add_comment")
                ]
            ]
            await update.message.reply_text(
                f"❌ **Invalid ticket number format**\n\n"
                f"You entered: `{ticket_number}`\n\n"
                f"📋 **Valid ticket number examples:**\n"
                f"• TH220925757\n"
                f"• VN00027\n"
                f"• IN00602\n\n"
                f"💡 **Tip:** If you want to add a comment, click the button below instead of typing here.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return WAITING_TICKET_NUMBER
        
        try:
            # Store ticket number in context for add comment functionality
            context.user_data['current_ticket_number'] = ticket_number
            
            # Get ticket comments from database
            comments = await self._get_ticket_comments(ticket_number)
            
            if not comments:
                await update.message.reply_text(
                    f"💬 **Ticket {ticket_number}**\n\n"
                    f"📝 No comments found for this ticket.\n"
                    f"✨ Be the first to add a comment!",
                    reply_markup=self._get_comments_keyboard(),
                    parse_mode='Markdown'
                )
                return VIEWING_COMMENTS
            
            # Format and display comments
            message = self._format_comments_display(ticket_number, comments)
            
            await update.message.reply_text(
                message,
                reply_markup=self._get_comments_keyboard(),
                parse_mode='HTML'
            )
            
            return VIEWING_COMMENTS
            
        except Exception as e:
            logger.error(f"Error getting ticket comments: {e}")
            await update.message.reply_text(
                f"❌ Error retrieving comments for ticket {ticket_number}. Please try again.",
                reply_markup=self._get_comments_keyboard()
            )
            return VIEWING_COMMENTS

    def _get_comments_keyboard(self):
        """Get keyboard for comments view"""
        keyboard = [
            [
                InlineKeyboardButton("⬅️ Back to My Tickets", callback_data="back_to_tickets"),
                InlineKeyboardButton("✍️ Add Comment", callback_data="add_comment")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _format_comments_display(self, ticket_number: str, comments: list) -> str:
        """Format comments for display"""
        message = f"💬 <b>Comments for Ticket {ticket_number}</b>\n"
        message += f"📊 Total: {len(comments)} comments\n\n"
        
        for i, comment in enumerate(comments, 1):
            author = comment.get('author_name', 'Unknown')
            date = comment.get('create_date', 'Unknown date')
            content = comment.get('body', 'No content')
            
            # Clean HTML tags from content
            import re
            content = re.sub(r'<[^>]+>', '', content)
            content = content.strip()
            
            message += f"<b>{i}. {author}</b>\n"
            message += f"📅 {date}\n"
            message += f"💬 {content}\n\n"
        
        return message

    async def _get_ticket_comments(self, ticket_number: str) -> list:
        """Get comments for a ticket by ticket number"""
        # This will need to be implemented in ticket_service
        return await self.ticket_service.get_ticket_comments_by_number(ticket_number)

    async def handle_add_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle add comment button click"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        logger.info(f"handle_add_comment: user_id={user_id}")
        
        # Check authentication
        if not self._is_authenticated(user_id):
            await query.edit_message_text("🔒 You need to login first. Use /login to authenticate.")
            return ConversationHandler.END
        
        # Check if we have current ticket number from view comments
        current_ticket_number = context.user_data.get('current_ticket_number')
        logger.info(f"Current ticket number in context: {current_ticket_number}")
        
        if current_ticket_number:
            # Use the current ticket number directly
            context.user_data['add_comment_ticket_number'] = current_ticket_number
            logger.info(f"Using current ticket number: {current_ticket_number}, moving to WAITING_COMMENT_TEXT")
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Comments", callback_data="back_to_comments")]
            ])
            
            await query.edit_message_text(
                f"📝 **Add Comment to Ticket {current_ticket_number}**\n\n"
                "Please enter your comment:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            return WAITING_COMMENT_TEXT
        else:
            # Ask for ticket number if not available
            logger.info("No current ticket number found, asking for ticket number input")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Tickets", callback_data="back_to_tickets")]
            ])
            
            await query.edit_message_text(
                "📝 **Add Comment to Ticket**\n\n"
                "Please enter the ticket number (e.g., VN00026, TH220925757):",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            return WAITING_ADD_COMMENT_TICKET

    async def handle_add_comment_ticket_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ticket number input for adding comment"""
        user_id = update.effective_user.id
        ticket_number = update.message.text.strip()
        
        logger.info(f"handle_add_comment_ticket_input: user_id={user_id}, ticket_number={ticket_number}")
        
        # Store ticket number in context
        context.user_data['add_comment_ticket_number'] = ticket_number
        
        # Ask for comment text
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Tickets", callback_data="back_to_tickets")]
        ])
        
        await update.message.reply_text(
            f"📝 **Add Comment to Ticket {ticket_number}**\n\n"
            "Please enter your comment:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        return WAITING_COMMENT_TEXT

    async def handle_comment_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle comment text input"""
        user_id = update.effective_user.id
        comment_text = update.message.text.strip()
        ticket_number = context.user_data.get('add_comment_ticket_number')
        
        logger.info(f"handle_comment_text_input: user_id={user_id}, ticket_number={ticket_number}")
        
        if not ticket_number:
            await update.message.reply_text("❌ Error: Ticket number not found. Please try again.")
            return ConversationHandler.END
        
        try:
            # Add comment to ticket
            success = await self.ticket_service.add_comment_to_ticket(ticket_number, comment_text, user_id, self.auth_service)
            
            if success:
                # Check if we came from view comments (has current_ticket_number)
                current_ticket = context.user_data.get('current_ticket_number')
                if current_ticket:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Comments", callback_data="back_to_comments")]
                    ])
                else:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Tickets", callback_data="back_to_tickets")]
                    ])
                
                await update.message.reply_text(
                    f"✅ **Comment Added Successfully!**\n\n"
                    f"**Ticket:** {ticket_number}\n"
                    f"**Comment:** {comment_text}",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to add comment to ticket {ticket_number}. Please check the ticket number and try again."
                )
            
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            await update.message.reply_text("❌ Error occurred while adding comment.")
        
        # Clear context data
        context.user_data.pop('add_comment_ticket_number', None)
        
        # Return to VIEWING_COMMENTS state so back_to_comments button works
        return VIEWING_COMMENTS

    def _is_valid_ticket_number(self, text: str) -> bool:
        """
        Validate if the input text looks like a valid ticket number
        
        Args:
            text: Input text to validate
            
        Returns:
            True if it looks like a ticket number, False otherwise
        """
        import re
        
        # Remove whitespace
        text = text.strip()
        
        # If text contains multiple words or is very long, likely a comment
        if ' ' in text or len(text) > 25:
            return False
        
        # If text is too short, also invalid
        if len(text) < 3:
            return False
        
        # Check for common comment indicators
        comment_indicators = [
            'this', 'that', 'please', 'help', 'issue', 'problem', 
            'bug', 'error', 'fix', 'need', 'want', 'can', 'could',
            'should', 'would', 'have', 'has', 'will', 'was', 'were',
            'hello', 'hi', 'thanks', 'thank', 'sorry'
        ]
        
        text_lower = text.lower()
        for indicator in comment_indicators:
            if indicator in text_lower:
                return False
        
        # Check if text contains typical ticket number patterns
        # Examples: TH220925757, VN00027, IN00602
        ticket_patterns = [
            r'^[A-Z]{2}\d{8,}$',  # TH220925757 format
            r'^[A-Z]{2}\d{5,7}$', # VN00027, IN00602 format  
            r'^[A-Z]{1,3}\d{3,}$', # General pattern with letters + numbers
            r'^\d{4,}$',          # Pure numbers (some systems use this)
        ]
        
        for pattern in ticket_patterns:
            if re.match(pattern, text.upper()):
                return True
        
        # If none of the patterns match and it doesn't look like a comment,
        # still give it a chance (could be a different ticket format)
        # But if it has special characters or looks like natural language, reject
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', text):
            return False
        
        # If it's all letters (no numbers), likely not a ticket number
        if text.isalpha():
            return False
            
        return True

    async def handle_awaiting_tickets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle view awaiting tickets callback"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if not self._is_authenticated(user_id):
            await query.edit_message_text("❌ Please authenticate first using /start")
            return ConversationHandler.END
        
        try:
            # Get awaiting tickets (chỉ những tickets có stage = "Waiting")
            awaiting_statuses = ['waiting']
            
            # Lấy tất cả tickets của user này
            all_tickets = await self.ticket_service.get_user_tickets(user_id, self.auth_service)
            
            # Lọc chỉ lấy tickets đang awaiting (stage = "Waiting")
            awaiting_tickets = []
            for ticket in all_tickets:
                status = ticket.get('stage_name', ticket.get('status', '')).lower()
                # Chỉ lấy tickets có trạng thái "Waiting"
                if status in awaiting_statuses:
                    awaiting_tickets.append(ticket)
            
            if not awaiting_tickets:
                await query.edit_message_text(
                    "📭 No awaiting tickets found.",
                    reply_markup=self.keyboards.get_back_to_tickets_keyboard()
                )
                return self.VIEWING_LIST
            
            # Simple awaiting tickets message
            message = "⏳ <b>Your Awaiting Tickets</b>\n\n"
            
            # Show count info
            if len(awaiting_tickets) > 10:
                message += f"📊 Found {len(awaiting_tickets)} awaiting tickets (showing first 10)\n"
            else:
                message += f"📊 Found {len(awaiting_tickets)} awaiting tickets\n"
            
            message += f"\n💡 <b>Use the buttons below to take action on each ticket.</b>\n\n"
            
            # Add instruction text as regular text - only for Mark Done section
            message += "📝 <b>Confirm to close tickets (Mark as Done):</b>"
            


            

            
            message += f"\n� <b>Click on the underlined links above to take action on tickets.</b>"
            
            keyboard = self.keyboards.get_awaiting_tickets_keyboard(awaiting_tickets)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return self.VIEWING_AWAITING
            
        except Exception as e:
            logger.error(f"Error viewing awaiting tickets for user {user_id}: {e}")
            await query.edit_message_text(
                "❌ Error loading awaiting tickets. Please try again.",
                reply_markup=self.keyboards.get_back_to_tickets_keyboard()
            )
            return self.VIEWING_LIST

    async def handle_awaiting_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle add comment for awaiting ticket"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if not self._is_authenticated(user_id):
            await query.edit_message_text("❌ Please authenticate first using /start")
            return ConversationHandler.END
        
        try:
            # Extract ticket ID from callback data
            ticket_id = query.data.split('_')[-1]
            
            # Store ticket ID in context for later use
            context.user_data['awaiting_comment_ticket_id'] = ticket_id
            
            await query.edit_message_text(
                f"💬 <b>Add Comment to Ticket #{ticket_id}</b>\n\n"
                f"Please enter your comment:",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard(),
                parse_mode='HTML'
            )
            
            return self.WAITING_AWAITING_COMMENT
            
        except Exception as e:
            logger.error(f"Error initiating comment for awaiting ticket: {e}")
            await query.edit_message_text(
                "❌ Error processing request. Please try again.",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
            )
            return self.VIEWING_AWAITING

    async def handle_awaiting_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle mark done for awaiting ticket"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if not self._is_authenticated(user_id):
            await query.edit_message_text("❌ Please authenticate first using /start")
            return ConversationHandler.END
        
        try:
            # Extract ticket ID from callback data
            ticket_id = query.data.split('_')[-1]
            
            # Mark ticket as resolved/done
            success = await self.ticket_service.update_ticket_status(ticket_id, 'resolved')
            
            if success:
                await query.edit_message_text(
                    f"✅ <b>Ticket #{ticket_id} marked as resolved!</b>\n\n"
                    f"The ticket status has been updated successfully.",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard(),
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    f"❌ <b>Failed to update Ticket #{ticket_id}</b>\n\n"
                    f"Please try again or contact support.",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard(),
                    parse_mode='HTML'
                )
            
            return self.VIEWING_AWAITING
            
        except Exception as e:
            logger.error(f"Error marking awaiting ticket as done: {e}")
            await query.edit_message_text(
                "❌ Error processing request. Please try again.",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
            )
            return self.VIEWING_AWAITING

    async def handle_awaiting_comment_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle comment text input for awaiting ticket"""
        user_id = update.message.from_user.id
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return ConversationHandler.END
        
        try:
            comment_text = update.message.text.strip()
            ticket_id = context.user_data.get('awaiting_comment_ticket_id')
            
            if not ticket_id:
                await update.message.reply_text(
                    "❌ Ticket ID not found. Please try again.",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
                )
                return self.VIEWING_AWAITING
            
            if not comment_text:
                await update.message.reply_text(
                    "❌ Comment cannot be empty. Please enter a valid comment or use 'Back to Awaiting' button to cancel:",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
                )
                return self.WAITING_AWAITING_COMMENT
            
            # Add comment to ticket
            success = await self.ticket_service.add_comment_to_ticket(ticket_id, comment_text, user_id, self.auth_service)
            
            if success:
                await update.message.reply_text(
                    f"✅ <b>Comment added successfully!</b>\n\n"
                    f"Your comment has been added to Ticket #{ticket_id}.",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard(),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Failed to add comment</b>\n\n"
                    f"Please try again or contact support.",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard(),
                    parse_mode='HTML'
                )
            
            # Clear stored ticket ID
            if 'awaiting_comment_ticket_id' in context.user_data:
                del context.user_data['awaiting_comment_ticket_id']
            
            return self.VIEWING_AWAITING
            
        except Exception as e:
            logger.error(f"Error adding comment to awaiting ticket: {e}")
            await update.message.reply_text(
                "❌ Error adding comment. Please try again.",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
            )
            return self.VIEWING_AWAITING

    async def handle_awaiting_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle click on ticket info (just answer the callback)"""
        query = update.callback_query
        await query.answer("ℹ️ Ticket information displayed above")
        return self.VIEWING_AWAITING

    async def handle_separator(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle click on separator (just answer the callback)"""
        query = update.callback_query
        await query.answer()
        return self.VIEWING_AWAITING

    async def handle_addcomment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /addcomment command from clickable links"""
        user_id = update.effective_user.id
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return
        
        try:
            # Extract ticket number from command arguments
            if context.args and len(context.args) > 0:
                ticket_number = context.args[0]
                
                # Store ticket number in context for comment flow
                context.user_data['awaiting_comment_ticket_id'] = ticket_number
                
                await update.message.reply_text(
                    f"💬 <b>Add Comment to Ticket #{ticket_number}</b>\n\n"
                    f"Please enter your comment:",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard(),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Invalid command format</b>\n\n"
                    f"Please use the clickable links in awaiting tickets view.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error handling addcomment command: {e}")
            await update.message.reply_text(
                "❌ Error processing add comment request. Please try again."
            )

    async def handle_markdone_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /markdone command from clickable links"""
        user_id = update.effective_user.id
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return
        
        try:
            # Extract ticket number from command arguments
            if context.args and len(context.args) > 0:
                ticket_number = context.args[0]
                
                # Mark ticket as resolved/done
                success = await self.ticket_service.update_ticket_status(ticket_number, 'resolved')
                
                if success:
                    await update.message.reply_text(
                        f"✅ <b>Ticket #{ticket_number} marked as resolved!</b>\n\n"
                        f"The ticket status has been updated successfully.\n\n"
                        f"Use /start → View My Tickets → Awaiting Tickets to see updated list.",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ <b>Failed to update Ticket #{ticket_number}</b>\n\n"
                        f"Please try again or contact support.",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ <b>Invalid command format</b>\n\n"
                    f"Please use the clickable links in awaiting tickets view.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error handling markdone command: {e}")
            await update.message.reply_text(
                "❌ Error processing mark done request. Please try again."
            )

    async def handle_global_comment_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle comment input from global context (outside conversation)"""
        user_id = update.effective_user.id
        
        # Check if user is waiting to add comment
        ticket_id = context.user_data.get('awaiting_comment_ticket_id')
        
        if ticket_id and self._is_authenticated(user_id):
            try:
                comment_text = update.message.text.strip()
                
                if not comment_text:
                    await update.message.reply_text(
                        "❌ Comment cannot be empty. Please enter a valid comment:"
                    )
                    return
                
                # Add comment to ticket
                success = await self.ticket_service.add_comment_to_ticket(
                    ticket_id, comment_text, user_id, self.auth_service
                )
                
                if success:
                    await update.message.reply_text(
                        f"✅ <b>Comment added successfully!</b>\n\n"
                        f"Your comment has been added to Ticket #{ticket_id}.\n\n"
                        f"Use /start → View My Tickets → Awaiting Tickets to see updated list.",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ <b>Failed to add comment</b>\n\n"
                        f"Please try again or contact support.",
                        parse_mode='HTML'
                    )
                
                # Clear stored ticket ID
                if 'awaiting_comment_ticket_id' in context.user_data:
                    del context.user_data['awaiting_comment_ticket_id']
                    
            except Exception as e:
                logger.error(f"Error adding comment to ticket {ticket_id}: {e}")
                await update.message.reply_text(
                    "❌ Error adding comment. Please try again."
                )
        # If not in comment mode, ignore the message (let other handlers process it)

    async def handle_addcomment_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ticket_number: str) -> None:
        """Handle add comment direct from deep link"""
        user_id = update.effective_user.id
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return
        
        try:
            # Store ticket number in context for comment flow
            context.user_data['awaiting_comment_ticket_id'] = ticket_number
            
            await update.message.reply_text(
                f"💬 <b>Add Comment to Ticket #{ticket_number}</b>\n\n"
                f"Please enter your comment:",
                parse_mode='HTML'
            )
                
        except Exception as e:
            logger.error(f"Error handling addcomment direct: {e}")
            await update.message.reply_text(
                "❌ Error processing add comment request. Please try again."
            )

    async def handle_markdone_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, ticket_number: str) -> None:
        """Handle mark done direct from deep link"""
        user_id = update.effective_user.id
        
        if not self._is_authenticated(user_id):
            await update.message.reply_text("❌ Please authenticate first using /start")
            return
        
        try:
            # Mark ticket as resolved/done
            success = await self.ticket_service.update_ticket_status(ticket_number, 'resolved')
            
            if success:
                await update.message.reply_text(
                    f"✅ <b>Ticket #{ticket_number} marked as resolved!</b>\n\n"
                    f"The ticket status has been updated successfully.\n\n"
                    f"Use /start → View My Tickets → Awaiting Tickets to see updated list.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ <b>Failed to update Ticket #{ticket_number}</b>\n\n"
                    f"Please try again or contact support.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error handling markdone direct: {e}")
            await update.message.reply_text(
                "❌ Error processing mark done request. Please try again."
            )
