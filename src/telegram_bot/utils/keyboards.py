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
        
        if has_tickets:
            # Add detail buttons for each ticket in a compact format
            if tickets:
                # Group detail buttons in rows of 2 for better space usage
                detail_buttons = []
                for i, ticket in enumerate(tickets, 1):
                    ticket_id = ticket.get('id')
                    if ticket_id:
                        detail_buttons.append(
                            InlineKeyboardButton(f"📄 {i}", callback_data=f"view_detail_{ticket_id}")
                        )
                
                # Add detail buttons in rows of 3 for compact layout
                for i in range(0, len(detail_buttons), 3):
                    row = detail_buttons[i:i+3]
                    keyboard.append(row)
                
                # Add separator
                keyboard.append([InlineKeyboardButton("────────────", callback_data="separator")])
            
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
    
