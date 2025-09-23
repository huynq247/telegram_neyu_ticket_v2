"""
Ticket-related keyboards for Telegram UI.
Handles all ticket navigation and action keyboards.
"""
from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from ...application.dto import TicketDTO


class TicketKeyboards:
    """Generates keyboards for ticket-related actions"""
    
    def get_main_tickets_keyboard(self) -> InlineKeyboardMarkup:
        """Get main tickets menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📋 My Tickets", callback_data="view_my_tickets"),
                InlineKeyboardButton("🆕 Create Ticket", callback_data="create_ticket")
            ],
            [
                InlineKeyboardButton("🔍 Search Tickets", callback_data="search_tickets"),
                InlineKeyboardButton("📊 Dashboard", callback_data="ticket_dashboard")
            ],
            [
                InlineKeyboardButton("💬 Recent Comments", callback_data="recent_comments"),
                InlineKeyboardButton("⚠️ Overdue Tickets", callback_data="overdue_tickets")
            ],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_list_keyboard(
        self, 
        tickets: List[TicketDTO],
        current_page: int = 1,
        total_pages: int = 1,
        show_filters: bool = True
    ) -> InlineKeyboardMarkup:
        """Get keyboard for ticket list"""
        keyboard = []
        
        # Ticket selection buttons (max 5 per page)
        for ticket in tickets[:5]:
            button_text = f"{ticket.status_emoji} {ticket.number} - {ticket.title[:25]}..."
            callback_data = f"view_ticket:{ticket.number}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Pagination if needed
        if total_pages > 1:
            nav_buttons = []
            if current_page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"tickets_page:{current_page-1}"))
            
            nav_buttons.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop"))
            
            if current_page < total_pages:
                nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"tickets_page:{current_page+1}"))
            
            keyboard.append(nav_buttons)
        
        # Action buttons
        action_buttons = []
        if show_filters:
            action_buttons.append(InlineKeyboardButton("🔍 Filter", callback_data="filter_tickets"))
        
        action_buttons.extend([
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_tickets"),
            InlineKeyboardButton("🆕 New", callback_data="create_ticket")
        ])
        
        keyboard.append(action_buttons)
        
        # Navigation
        keyboard.append([InlineKeyboardButton("🔙 Back to Tickets Menu", callback_data="tickets_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_details_keyboard(
        self, 
        ticket_number: str,
        can_modify: bool = False,
        comment_count: int = 0
    ) -> InlineKeyboardMarkup:
        """Get keyboard for ticket details view"""
        keyboard = []
        
        # Comment actions
        comment_buttons = []
        if comment_count > 0:
            comment_buttons.append(InlineKeyboardButton("💬 View Comments", callback_data=f"view_comments:{ticket_number}"))
        
        comment_buttons.append(InlineKeyboardButton("➕ Add Comment", callback_data=f"add_comment:{ticket_number}"))
        
        keyboard.append(comment_buttons)
        
        # Ticket actions
        if can_modify:
            modify_buttons = [
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_ticket:{ticket_number}"),
                InlineKeyboardButton("🏷️ Change Status", callback_data=f"change_status:{ticket_number}")
            ]
            keyboard.append(modify_buttons)
        
        # Information actions
        info_buttons = [
            InlineKeyboardButton("📋 Full Details", callback_data=f"full_details:{ticket_number}"),
            InlineKeyboardButton("📈 History", callback_data=f"ticket_history:{ticket_number}")
        ]
        keyboard.append(info_buttons)
        
        # Navigation
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_ticket:{ticket_number}"),
            InlineKeyboardButton("🔙 Back to List", callback_data="view_my_tickets")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_filters_keyboard(
        self,
        current_status: Optional[str] = None,
        current_priority: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """Get keyboard for ticket filtering"""
        keyboard = []
        
        # Status filters
        keyboard.append([InlineKeyboardButton("📊 Filter by Status", callback_data="filter_header_status")])
        
        status_buttons = []
        statuses = [("🟢 Open", "Open"), ("🟡 In Progress", "In Progress"), ("🔵 Resolved", "Resolved"), ("⚫ Closed", "Closed")]
        
        for emoji_text, status in statuses:
            callback_data = f"filter_status:{status}"
            if current_status == status:
                emoji_text += " ✓"
            status_buttons.append(InlineKeyboardButton(emoji_text, callback_data=callback_data))
        
        # Split into 2 rows
        keyboard.append(status_buttons[:2])
        keyboard.append(status_buttons[2:])
        
        # Priority filters
        keyboard.append([InlineKeyboardButton("⚡ Filter by Priority", callback_data="filter_header_priority")])
        
        priority_buttons = []
        priorities = [("🟢 Low", "Low"), ("🟡 Medium", "Medium"), ("🟠 High", "High"), ("🔴 Urgent", "Urgent")]
        
        for emoji_text, priority in priorities:
            callback_data = f"filter_priority:{priority}"
            if current_priority == priority:
                emoji_text += " ✓"
            priority_buttons.append(InlineKeyboardButton(emoji_text, callback_data=callback_data))
        
        # Split into 2 rows
        keyboard.append(priority_buttons[:2])
        keyboard.append(priority_buttons[2:])
        
        # Clear and apply
        keyboard.append([
            InlineKeyboardButton("🗑️ Clear Filters", callback_data="clear_filters"),
            InlineKeyboardButton("✅ Apply Filters", callback_data="apply_filters")
        ])
        
        # Navigation
        keyboard.append([InlineKeyboardButton("🔙 Back to Tickets", callback_data="view_my_tickets")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_search_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for ticket search"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Search by Title", callback_data="search_by_title"),
                InlineKeyboardButton("📝 Search by Content", callback_data="search_by_content")
            ],
            [
                InlineKeyboardButton("🏷️ Search by Number", callback_data="search_by_number"),
                InlineKeyboardButton("👤 Search by Creator", callback_data="search_by_creator")
            ],
            [
                InlineKeyboardButton("🔄 Recent Searches", callback_data="recent_searches"),
                InlineKeyboardButton("🌐 Advanced Search", callback_data="advanced_search")
            ],
            [InlineKeyboardButton("🔙 Back to Tickets", callback_data="tickets_menu")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_dashboard_keyboard(self) -> InlineKeyboardMarkup:
        """Get keyboard for ticket dashboard"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status Overview", callback_data="status_overview"),
                InlineKeyboardButton("📈 My Statistics", callback_data="my_statistics")
            ],
            [
                InlineKeyboardButton("⚠️ Overdue Tickets", callback_data="overdue_tickets"),
                InlineKeyboardButton("🎯 High Priority", callback_data="high_priority_tickets")
            ],
            [
                InlineKeyboardButton("📅 This Week", callback_data="tickets_this_week"),
                InlineKeyboardButton("📆 This Month", callback_data="tickets_this_month")
            ],
            [
                InlineKeyboardButton("🔄 Refresh Dashboard", callback_data="refresh_dashboard"),
                InlineKeyboardButton("🔙 Back to Tickets", callback_data="tickets_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_status_change_keyboard(self, ticket_number: str, current_status: str) -> InlineKeyboardMarkup:
        """Get keyboard for changing ticket status"""
        keyboard = []
        
        keyboard.append([InlineKeyboardButton("🏷️ Change Status", callback_data="status_header")])
        
        # Available status transitions (simplified)
        status_options = []
        
        if current_status == "Open":
            status_options = [("🟡 In Progress", "In Progress"), ("🔵 Resolved", "Resolved")]
        elif current_status == "In Progress":
            status_options = [("🟢 Open", "Open"), ("🔵 Resolved", "Resolved")]
        elif current_status == "Resolved":
            status_options = [("🟢 Reopen", "Open"), ("⚫ Close", "Closed")]
        elif current_status == "Closed":
            status_options = [("🟢 Reopen", "Open")]
        
        for text, status in status_options:
            callback_data = f"set_status:{ticket_number}:{status}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        
        # Navigation
        keyboard.append([
            InlineKeyboardButton("❌ Cancel", callback_data=f"view_ticket:{ticket_number}"),
            InlineKeyboardButton("🔙 Back", callback_data=f"view_ticket:{ticket_number}")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_create_ticket_keyboard(self) -> ReplyKeyboardMarkup:
        """Get keyboard for ticket creation process"""
        keyboard = [
            [KeyboardButton("❌ Cancel Creation")],
            [KeyboardButton("💡 Help"), KeyboardButton("📝 Templates")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    def get_quick_actions_keyboard(self) -> ReplyKeyboardMarkup:
        """Get quick actions keyboard"""
        keyboard = [
            [KeyboardButton("📋 My Tickets"), KeyboardButton("🆕 Create Ticket")],
            [KeyboardButton("💬 Comments"), KeyboardButton("🔍 Search")],
            [KeyboardButton("📊 Dashboard"), KeyboardButton("🔙 Main Menu")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_ticket_actions_inline_keyboard(self, ticket_number: str) -> InlineKeyboardMarkup:
        """Get inline keyboard for quick ticket actions"""
        keyboard = [
            [
                InlineKeyboardButton("👁️ View", callback_data=f"view_ticket:{ticket_number}"),
                InlineKeyboardButton("💬 Comments", callback_data=f"view_comments:{ticket_number}")
            ],
            [
                InlineKeyboardButton("➕ Add Comment", callback_data=f"add_comment:{ticket_number}"),
                InlineKeyboardButton("📋 Details", callback_data=f"full_details:{ticket_number}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)