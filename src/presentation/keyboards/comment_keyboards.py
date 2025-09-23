"""
Comment-related keyboards for Telegram UI.
Handles all comment navigation and action keyboards.
"""
from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from ...application.dto import TicketDTO, CommentDTO


class CommentKeyboards:
    """Generates keyboards for comment-related actions"""
    
    def get_recent_tickets_keyboard(self, tickets: List[TicketDTO]) -> InlineKeyboardMarkup:
        """Get keyboard for recent tickets selection"""
        keyboard = []
        
        # Add ticket selection buttons (max 10)
        for ticket in tickets[:10]:
            button_text = f"{ticket.status_emoji} {ticket.number} - {ticket.title[:25]}..."
            callback_data = f"view_comments:{ticket.number}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("🔍 Search Tickets", callback_data="search_tickets_for_comments"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_recent_tickets")
        ])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_ticket_comments_keyboard(
        self, 
        ticket_number: str, 
        has_comments: bool = True,
        can_add_comment: bool = True,
        can_add_internal: bool = False
    ) -> InlineKeyboardMarkup:
        """Get keyboard for ticket comments view"""
        keyboard = []
        
        # Comments actions
        if has_comments:
            keyboard.append([
                InlineKeyboardButton("📖 View All Comments", callback_data=f"view_all_comments:{ticket_number}"),
                InlineKeyboardButton("🔍 Search Comments", callback_data=f"search_comments:{ticket_number}")
            ])
        
        # Add comment buttons
        if can_add_comment:
            add_buttons = [InlineKeyboardButton("➕ Add Comment", callback_data=f"add_comment:{ticket_number}")]
            
            if can_add_internal:
                add_buttons.append(InlineKeyboardButton("🔒 Internal Note", callback_data=f"add_internal:{ticket_number}"))
            
            keyboard.append(add_buttons)
        
        # Quick templates
        if can_add_comment:
            keyboard.append([InlineKeyboardButton("📝 Quick Templates", callback_data=f"comment_templates:{ticket_number}")])
        
        # Navigation
        keyboard.append([
            InlineKeyboardButton("🎫 Ticket Details", callback_data=f"ticket_details:{ticket_number}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_comments:{ticket_number}")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Tickets", callback_data="back_to_ticket_list")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_templates_keyboard(self, ticket_number: str, templates: List[str]) -> InlineKeyboardMarkup:
        """Get keyboard for comment templates"""
        keyboard = []
        
        # Template buttons (max 8)
        for i, template in enumerate(templates[:8]):
            button_text = f"{i+1}️⃣ {template[:30]}..."
            callback_data = f"use_template:{ticket_number}:{i}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Custom comment option
        keyboard.append([InlineKeyboardButton("✏️ Type Custom Comment", callback_data=f"custom_comment:{ticket_number}")])
        
        # Navigation
        keyboard.append([
            InlineKeyboardButton("🔙 Back to Comments", callback_data=f"view_comments:{ticket_number}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_comment")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_type_keyboard(self, ticket_number: str) -> InlineKeyboardMarkup:
        """Get keyboard for selecting comment type"""
        keyboard = [
            [InlineKeyboardButton("💬 Public Comment", callback_data=f"comment_type:{ticket_number}:public")],
            [InlineKeyboardButton("🔒 Internal Note", callback_data=f"comment_type:{ticket_number}:internal")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"view_comments:{ticket_number}")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_actions_keyboard(
        self, 
        comment_id: int, 
        ticket_number: str,
        can_edit: bool = False,
        can_reply: bool = True
    ) -> InlineKeyboardMarkup:
        """Get keyboard for individual comment actions"""
        keyboard = []
        
        # Comment actions
        actions = []
        if can_reply:
            actions.append(InlineKeyboardButton("↩️ Reply", callback_data=f"reply_comment:{comment_id}"))
        
        if can_edit:
            actions.append(InlineKeyboardButton("✏️ Edit", callback_data=f"edit_comment:{comment_id}"))
        
        if actions:
            keyboard.append(actions)
        
        # Navigation
        keyboard.append([
            InlineKeyboardButton("📖 View Thread", callback_data=f"view_thread:{comment_id}"),
            InlineKeyboardButton("🔙 Back to Comments", callback_data=f"view_comments:{ticket_number}")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_confirmation_keyboard(
        self, 
        ticket_number: str, 
        has_warnings: bool = False
    ) -> InlineKeyboardMarkup:
        """Get keyboard for comment confirmation"""
        keyboard = []
        
        if has_warnings:
            keyboard.append([
                InlineKeyboardButton("✅ Post Anyway", callback_data=f"confirm_comment:{ticket_number}"),
                InlineKeyboardButton("✏️ Edit Comment", callback_data=f"edit_comment_draft:{ticket_number}")
            ])
        else:
            keyboard.append([InlineKeyboardButton("✅ Post Comment", callback_data=f"confirm_comment:{ticket_number}")])
        
        keyboard.append([
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_comment"),
            InlineKeyboardButton("🔙 Back", callback_data=f"view_comments:{ticket_number}")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_search_keyboard(self, ticket_number: Optional[str] = None) -> InlineKeyboardMarkup:
        """Get keyboard for comment search"""
        keyboard = []
        
        # Search options
        if ticket_number:
            keyboard.append([
                InlineKeyboardButton("🔍 Search This Ticket", callback_data=f"search_ticket_comments:{ticket_number}"),
                InlineKeyboardButton("🌐 Search All Comments", callback_data="search_all_comments")
            ])
            back_callback = f"view_comments:{ticket_number}"
        else:
            keyboard.append([InlineKeyboardButton("🔍 Start Search", callback_data="start_comment_search")])
            back_callback = "back_to_ticket_list"
        
        # Navigation
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=back_callback)])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_pagination_keyboard(
        self, 
        ticket_number: str, 
        current_page: int, 
        total_pages: int
    ) -> InlineKeyboardMarkup:
        """Get keyboard for comment pagination"""
        keyboard = []
        
        # Pagination buttons
        nav_buttons = []
        
        if current_page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"comments_page:{ticket_number}:{current_page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop"))
        
        if current_page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"comments_page:{ticket_number}:{current_page+1}"))
        
        keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.append([
            InlineKeyboardButton("➕ Add Comment", callback_data=f"add_comment:{ticket_number}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_comments:{ticket_number}")
        ])
        
        # Navigation
        keyboard.append([InlineKeyboardButton("🔙 Back to Tickets", callback_data="back_to_ticket_list")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_comment_success_keyboard(self, ticket_number: str) -> InlineKeyboardMarkup:
        """Get keyboard after successful comment addition"""
        keyboard = [
            [
                InlineKeyboardButton("📖 View Comments", callback_data=f"view_comments:{ticket_number}"),
                InlineKeyboardButton("➕ Add Another", callback_data=f"add_comment:{ticket_number}")
            ],
            [
                InlineKeyboardButton("🎫 Ticket Details", callback_data=f"ticket_details:{ticket_number}"),
                InlineKeyboardButton("🔙 Back to Tickets", callback_data="back_to_ticket_list")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_reply_keyboard_for_input(self) -> ReplyKeyboardMarkup:
        """Get reply keyboard for text input"""
        keyboard = [
            [KeyboardButton("❌ Cancel")],
            [KeyboardButton("📝 Templates"), KeyboardButton("💡 Help")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    def get_thread_keyboard(
        self, 
        parent_comment_id: int, 
        ticket_number: str,
        can_reply: bool = True
    ) -> InlineKeyboardMarkup:
        """Get keyboard for comment thread view"""
        keyboard = []
        
        if can_reply:
            keyboard.append([InlineKeyboardButton("↩️ Reply to Thread", callback_data=f"reply_thread:{parent_comment_id}")])
        
        keyboard.append([
            InlineKeyboardButton("📖 All Comments", callback_data=f"view_comments:{ticket_number}"),
            InlineKeyboardButton("🔄 Refresh Thread", callback_data=f"refresh_thread:{parent_comment_id}")
        ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Comments", callback_data=f"view_comments:{ticket_number}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_quick_actions_keyboard(self, ticket_number: str) -> ReplyKeyboardMarkup:
        """Get quick actions reply keyboard"""
        keyboard = [
            [KeyboardButton("💬 Add Comment"), KeyboardButton("📖 View Comments")],
            [KeyboardButton("🎫 Ticket Details"), KeyboardButton("🔍 Search")],
            [KeyboardButton("🔙 Back to Menu")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)