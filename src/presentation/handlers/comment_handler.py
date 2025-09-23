"""
Focused comment handler for Telegram bot.
Handles comment-related interactions with clean separation of concerns.
"""
from typing import Optional, Dict, Any
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging

from ...application import (
    ViewCommentsUseCase, 
    AddCommentUseCase,
    ViewCommentsRequest,
    AddCommentRequest
)
from ..formatters.comment_formatter import CommentFormatter
from ..keyboards.comment_keyboards import CommentKeyboards

logger = logging.getLogger(__name__)


class CommentHandler:
    """Focused handler for comment operations"""
    
    def __init__(
        self,
        view_comments_use_case: ViewCommentsUseCase,
        add_comment_use_case: AddCommentUseCase,
        formatter: CommentFormatter,
        keyboards: CommentKeyboards
    ):
        self.view_comments_use_case = view_comments_use_case
        self.add_comment_use_case = add_comment_use_case
        self.formatter = formatter
        self.keyboards = keyboards
    
    async def handle_view_comments_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle initial request to view comments"""
        user_id = update.effective_user.id
        
        try:
            # Get user email from context (set during authentication)
            user_email = context.user_data.get('email')
            if not user_email:
                await update.message.reply_text("❌ Authentication required. Please start with /start")
                return "END"
            
            # Get recent tickets user can comment on
            recent_tickets = await self.view_comments_use_case.search_tickets_for_comments(
                user_email=user_email,
                query="",  # Empty query gets recent tickets
                limit=10
            )
            
            if not recent_tickets:
                await update.message.reply_text(
                    "📋 You don't have any recent tickets to view comments on.\n\n"
                    "💡 Create a ticket first or contact support."
                )
                return "END"
            
            # Format and send ticket selection
            message = self.formatter.format_recent_tickets_for_comments(recent_tickets)
            keyboard = self.keyboards.get_recent_tickets_keyboard(recent_tickets)
            
            await update.message.reply_text(
                message, 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )
            
            # Store tickets in context for quick access
            context.user_data['recent_tickets'] = [t.to_dict() for t in recent_tickets]
            
            return "WAITING_TICKET_SELECTION"
            
        except Exception as e:
            logger.error(f"Error in handle_view_comments_start: {e}")
            await update.message.reply_text("❌ Error loading tickets. Please try again.")
            return "END"
    
    async def handle_ticket_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle ticket selection for viewing comments"""
        query = update.callback_query
        await query.answer()
        
        try:
            user_email = context.user_data.get('email')
            
            # Parse callback data: "view_comments:TICKET_NUMBER"
            if not query.data.startswith("view_comments:"):
                await query.edit_message_text("❌ Invalid selection. Please try again.")
                return "END"
            
            ticket_number = query.data.split(":")[1]
            
            # Get comments for the ticket
            request = ViewCommentsRequest(
                ticket_number=ticket_number,
                user_email=user_email
            )
            
            response = await self.view_comments_use_case.execute(request)
            
            # Format and display comments
            message = self.formatter.format_comments_list(response.ticket, response.comments)
            keyboard = self.keyboards.get_ticket_comments_keyboard(
                ticket_number=ticket_number,
                has_comments=len(response.comments) > 0,
                can_add_comment=response.user_can_add_comment,
                can_add_internal=response.user_can_add_internal_comment
            )
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # Store current ticket in context
            context.user_data['current_ticket'] = response.ticket.to_dict()
            context.user_data['current_comments'] = [c.to_dict() for c in response.comments]
            
            return "VIEWING_COMMENTS"
            
        except Exception as e:
            logger.error(f"Error in handle_ticket_selection: {e}")
            await query.edit_message_text("❌ Error loading comments. Please try again.")
            return "END"
    
    async def handle_add_comment_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle request to add a comment"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data: "add_comment:TICKET_NUMBER" or "add_internal:TICKET_NUMBER"
            callback_parts = query.data.split(":")
            comment_type = "internal" if callback_parts[0] == "add_internal" else "public"
            ticket_number = callback_parts[1]
            
            # Store comment context
            context.user_data['adding_comment'] = {
                'ticket_number': ticket_number,
                'comment_type': comment_type
            }
            
            # Get comment templates
            user_email = context.user_data.get('email')
            templates = await self.add_comment_use_case.get_comment_templates(user_email, ticket_number)
            
            if templates:
                # Show templates
                message = self.formatter.format_comment_templates(templates)
                keyboard = self.keyboards.get_comment_templates_keyboard(ticket_number, templates)
                
                await query.edit_message_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                context.user_data['comment_templates'] = templates
                return "SELECTING_TEMPLATE"
            else:
                # Go straight to text input
                await query.edit_message_text(
                    f"✏️ **Type your {'internal note' if comment_type == 'internal' else 'comment'}:**\n\n"
                    f"🎫 **Ticket:** {ticket_number}\n\n"
                    "💡 **Tip:** Keep it clear and helpful!",
                    reply_markup=self.keyboards.get_reply_keyboard_for_input(),
                    parse_mode='Markdown'
                )
                
                return "TYPING_COMMENT"
                
        except Exception as e:
            logger.error(f"Error in handle_add_comment_start: {e}")
            await query.edit_message_text("❌ Error starting comment addition. Please try again.")
            return "END"
    
    async def handle_template_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle comment template selection"""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data.startswith("use_template:"):
                # Parse: "use_template:TICKET_NUMBER:INDEX"
                parts = query.data.split(":")
                ticket_number = parts[1]
                template_index = int(parts[2])
                
                templates = context.user_data.get('comment_templates', [])
                if template_index < len(templates):
                    selected_template = templates[template_index]
                    
                    # Store selected template as comment draft
                    context.user_data['comment_draft'] = selected_template
                    
                    # Show confirmation
                    message = f"📝 **Review your comment:**\n\n"
                    message += f"🎫 **Ticket:** {ticket_number}\n\n"
                    message += f"💬 **Comment:**\n{selected_template}\n\n"
                    message += "✅ **Post this comment?**"
                    
                    keyboard = self.keyboards.get_comment_confirmation_keyboard(ticket_number)
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    
                    return "CONFIRMING_COMMENT"
                    
            elif query.data.startswith("custom_comment:"):
                # User wants to type custom comment
                ticket_number = query.data.split(":")[1]
                
                await query.edit_message_text(
                    f"✏️ **Type your comment:**\n\n"
                    f"🎫 **Ticket:** {ticket_number}\n\n"
                    "💡 **Tip:** Be specific and helpful!",
                    parse_mode='Markdown'
                )
                
                # Remove inline keyboard and show reply keyboard
                await update.effective_chat.send_message(
                    "Type your comment below:",
                    reply_markup=self.keyboards.get_reply_keyboard_for_input()
                )
                
                return "TYPING_COMMENT"
                
        except Exception as e:
            logger.error(f"Error in handle_template_selection: {e}")
            await query.edit_message_text("❌ Error processing template selection.")
            return "END"
    
    async def handle_comment_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle user typing comment text"""
        message_text = update.message.text
        
        if message_text == "❌ Cancel":
            await update.message.reply_text(
                "❌ Comment cancelled.",
                reply_markup=ReplyKeyboardRemove()
            )
            return "END"
        
        try:
            comment_context = context.user_data.get('adding_comment', {})
            ticket_number = comment_context.get('ticket_number')
            user_email = context.user_data.get('email')
            
            if not ticket_number:
                await update.message.reply_text("❌ Error: No ticket selected. Please start over.")
                return "END"
            
            # Validate comment content
            warnings = await self.add_comment_use_case.validate_comment_content(message_text, user_email)
            
            # Store comment draft
            context.user_data['comment_draft'] = message_text
            
            if warnings:
                # Show warnings
                warning_message = self.formatter.format_comment_validation_warning(warnings)
                keyboard = self.keyboards.get_comment_confirmation_keyboard(ticket_number, has_warnings=True)
                
                await update.message.reply_text(
                    warning_message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                return "CONFIRMING_COMMENT"
            else:
                # No warnings, show direct confirmation
                message = f"📝 **Review your comment:**\n\n"
                message += f"🎫 **Ticket:** {ticket_number}\n\n"
                message += f"💬 **Comment:**\n{message_text}\n\n"
                message += "✅ **Post this comment?**"
                
                keyboard = self.keyboards.get_comment_confirmation_keyboard(ticket_number)
                
                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                return "CONFIRMING_COMMENT"
                
        except Exception as e:
            logger.error(f"Error in handle_comment_text_input: {e}")
            await update.message.reply_text("❌ Error processing your comment. Please try again.")
            return "END"
    
    async def handle_comment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle comment confirmation and posting"""
        query = update.callback_query
        await query.answer()
        
        try:
            if not query.data.startswith("confirm_comment:"):
                await query.edit_message_text("❌ Invalid action.")
                return "END"
            
            ticket_number = query.data.split(":")[1]
            comment_context = context.user_data.get('adding_comment', {})
            comment_draft = context.user_data.get('comment_draft')
            user_email = context.user_data.get('email')
            
            if not all([ticket_number, comment_draft, user_email]):
                await query.edit_message_text("❌ Error: Missing comment information.")
                return "END"
            
            # Create and execute add comment request
            request = AddCommentRequest(
                ticket_number=ticket_number,
                content=comment_draft,
                author_email=user_email,
                comment_type=comment_context.get('comment_type', 'public')
            )
            
            response = await self.add_comment_use_case.execute(request)
            
            # Show success message
            current_ticket = context.user_data.get('current_ticket', {})
            success_message = self.formatter.format_comment_added_success(
                response.comment, 
                current_ticket
            )
            keyboard = self.keyboards.get_comment_success_keyboard(ticket_number)
            
            await query.edit_message_text(
                success_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # Clean up context
            context.user_data.pop('adding_comment', None)
            context.user_data.pop('comment_draft', None)
            context.user_data.pop('comment_templates', None)
            
            return "COMMENT_POSTED"
            
        except Exception as e:
            logger.error(f"Error in handle_comment_confirmation: {e}")
            await query.edit_message_text("❌ Error posting comment. Please try again.")
            return "END"
    
    async def handle_refresh_comments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Handle refresh comments request"""
        query = update.callback_query
        await query.answer("🔄 Refreshing...")
        
        try:
            ticket_number = query.data.split(":")[1]
            user_email = context.user_data.get('email')
            
            # Refresh comments
            request = ViewCommentsRequest(
                ticket_number=ticket_number,
                user_email=user_email
            )
            
            response = await self.view_comments_use_case.execute(request)
            
            # Update display
            message = self.formatter.format_comments_list(response.ticket, response.comments)
            keyboard = self.keyboards.get_ticket_comments_keyboard(
                ticket_number=ticket_number,
                has_comments=len(response.comments) > 0,
                can_add_comment=response.user_can_add_comment,
                can_add_internal=response.user_can_add_internal_comment
            )
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            return "VIEWING_COMMENTS"
            
        except Exception as e:
            logger.error(f"Error in handle_refresh_comments: {e}")
            await query.edit_message_text("❌ Error refreshing comments.")
            return "END"
    
    def get_user_email(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        """Helper to get user email from context"""
        return context.user_data.get('email')
    
    def get_user_permissions(self, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """Helper to get user permissions from context"""
        return context.user_data.get('permissions', {})