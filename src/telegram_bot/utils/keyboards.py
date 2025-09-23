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
            [InlineKeyboardButton("🇮🇩 Indonesia", callback_data="dest_Indonesia")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
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
            [InlineKeyboardButton("❓ Help", callback_data="menu_help")],
            [InlineKeyboardButton("🚪 Log out", callback_data="menu_logout")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_ticket_list_keyboard(current_page: int = 1, total_pages: int = 1, has_tickets: bool = True, tickets: list = None):
        """
        Keyboard for ticket list navigation
        
        Args:
            current_page: Current page number
            total_pages: Total number of pages
            has_tickets: Whether user has tickets
            tickets: List of tickets to create detail buttons
        """
        keyboard = []
        
        # Main options
        keyboard.append([
            InlineKeyboardButton("🔍 Search", callback_data="view_search"),
            InlineKeyboardButton("⏳ Awaiting Tickets", callback_data="view_awaiting")
        ])
        
        # Comment options
        keyboard.append([
            InlineKeyboardButton("👁 View Comments", callback_data="view_comments")
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
    
    @staticmethod
    def get_awaiting_tickets_keyboard(tickets: list = None):
        """
        Keyboard for awaiting tickets view with detailed action buttons
        
        Args:
            tickets: List of awaiting tickets to create action buttons for
        """
        keyboard = []
        done_buttons = []
        comment_buttons = []
        
        if tickets:
            for ticket in tickets:
                ticket_number = ticket.get('tracking_id', ticket.get('number', 'N/A'))
                status = ticket.get('stage_name', 'Unknown')
                
                # Format date safely
                create_date = ticket.get('create_date')
                if create_date:
                    try:
                        from datetime import datetime
                        if isinstance(create_date, str):
                            if len(create_date) >= 10:
                                date = create_date[:10]
                            else:
                                date = str(create_date)
                        elif hasattr(create_date, 'strftime'):
                            date = create_date.strftime('%Y-%m-%d')
                        else:
                            date = str(create_date)
                    except:
                        date = 'N/A'
                else:
                    date = 'N/A'
                    
                assignee = ticket.get('user_name', 'Unassigned')
                
                # Group buttons by function with clear sections
                short_status = status[:12] if len(status) > 12 else status
                short_assignee = assignee[:12] if len(assignee) > 12 else assignee
                
                # Mark Done button - simplified with only essential info
                done_text = f"✅ Mark Done | {ticket_number} | {short_status}"
                done_buttons.append(InlineKeyboardButton(done_text, callback_data=f"awaiting_done_{ticket_number}"))
                
                # Add Comment button with ticket info
                comment_text = f"💬 Add Comment\n📋 {ticket_number} | 📊 {short_status}"
                comment_buttons.append(InlineKeyboardButton(comment_text, callback_data=f"awaiting_comment_{ticket_number}"))
            
            # Add grouped buttons without header buttons
            if done_buttons:
                # Add all done buttons
                for btn in done_buttons:
                    keyboard.append([btn])
            
            # Add spacing and instruction before comment buttons
            if done_buttons and comment_buttons:
                keyboard.append([InlineKeyboardButton("───────────────", callback_data="spacer")])
                # Add instruction text for comment section
                keyboard.append([InlineKeyboardButton("💭 If issues remain, add comments before closing:", callback_data="comment_instruction")])
            
            if comment_buttons:
                # Add all comment buttons
                for btn in comment_buttons:
                    keyboard.append([btn])
        
        # Navigation button
        keyboard.append([
            InlineKeyboardButton("🔙 Back to List", callback_data="view_back_to_list")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_ticket_detail_keyboard(ticket_id: int):
        """
        Keyboard for ticket detail view
        
        Args:
            ticket_id: ID of the ticket
        """
        keyboard = [
            [
                InlineKeyboardButton("📝 Edit", callback_data=f"ticket_edit_{ticket_id}"),
                InlineKeyboardButton("⚡ Change Priority", callback_data=f"ticket_priority_{ticket_id}")
            ],
            [
                InlineKeyboardButton("🔒 Close Ticket", callback_data=f"ticket_close_{ticket_id}"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"ticket_refresh_{ticket_id}")
            ],
            [InlineKeyboardButton("⬅️ Back to List", callback_data="view_back_to_list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # REMOVED - Filter keyboards no longer needed
    # @staticmethod
    # def get_status_filter_keyboard():
    #     """Keyboard for status filtering"""
    #     keyboard = [
    #         [
    #             InlineKeyboardButton("🆕 New", callback_data="filter_status_new"),
    #             InlineKeyboardButton("🔄 In Progress", callback_data="filter_status_progress")
    #         ],
    #         [
    #             InlineKeyboardButton("✅ Done", callback_data="filter_status_done"),
    #             InlineKeyboardButton("❌ Cancelled", callback_data="filter_status_cancelled")
    #         ],
    #         [
    #             InlineKeyboardButton("🔍 All Status", callback_data="filter_status_all")
    #         ],
    #         [InlineKeyboardButton("⬅️ Back", callback_data="view_back_to_list")]
    #     ]
    #     return InlineKeyboardMarkup(keyboard)
    # 
    # @staticmethod
    # def get_priority_filter_keyboard():
    #     """Keyboard for priority filtering"""
    #     keyboard = [
    #         [
    #             InlineKeyboardButton("🔴 Urgent (4)", callback_data="filter_priority_4"),
    #             InlineKeyboardButton("🟠 High (3)", callback_data="filter_priority_3")
    #         ],
    #         [
    #             InlineKeyboardButton("🟡 Normal (2)", callback_data="filter_priority_2"),
    #             InlineKeyboardButton("🟢 Low (1)", callback_data="filter_priority_1")
    #         ],
    #         [
    #             InlineKeyboardButton("🔍 All Priorities", callback_data="filter_priority_all")
    #         ],
    #         [InlineKeyboardButton("⬅️ Back", callback_data="view_back_to_list")]
    #     ]
    #     return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_search_result_keyboard(current_page: int = 1, total_pages: int = 1):
        """Keyboard for search results"""
        keyboard = []
        
        # Pagination for search results
        if total_pages > 1:
            pagination_row = []
            if current_page > 1:
                pagination_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"search_page_{current_page-1}"))
            
            pagination_row.append(InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="search_page_info"))
            
            if current_page < total_pages:
                pagination_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"search_page_{current_page+1}"))
            
            keyboard.append(pagination_row)
        
        keyboard.extend([
            [InlineKeyboardButton("🔍 New Search", callback_data="view_search")],
            [InlineKeyboardButton("⬅️ Back to List", callback_data="view_back_to_list")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_to_menu_keyboard():
        """Simple keyboard with just Back to Menu button"""
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_login_keyboard():
        """Login keyboard for unauthenticated users"""
        keyboard = [
            [InlineKeyboardButton("🔐 Login", callback_data="start_login")],
            [InlineKeyboardButton("❓ Help", callback_data="show_help")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_to_awaiting_keyboard():
        """Keyboard to go back to awaiting tickets view"""
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Awaiting", callback_data="view_awaiting")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_to_tickets_keyboard():
        """Keyboard to go back to tickets list"""
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Tickets", callback_data="view_back_to_list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
