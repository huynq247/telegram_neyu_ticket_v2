"""
Ticket Comment Handler Module

This module handles all comment-related operations for tickets including:
- Viewing ticket comments  
- Adding new comments
- Comment validation and formatting
"""

import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from .base_view_handler import BaseViewHandler, WAITING_TICKET_NUMBER, VIEWING_COMMENTS, WAITING_COMMENT_TEXT, WAITING_ADD_COMMENT_TICKET

logger = logging.getLogger(__name__)


class TicketCommentHandler(BaseViewHandler):
    """Handler for ticket comment operations"""
    
    def __init__(self, ticket_service, auth_service):
        """Initialize comment handler"""
        super().__init__(ticket_service, auth_service)
    
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

    async def handle_back_to_comments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle back to comments button click"""
        query = update.callback_query
        user_id = update.effective_user.id
        
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
            # No current ticket, go back to ticket selection
            await query.edit_message_text(
                "🎫 Please enter the ticket number to view comments:\n\n"
                "Example: TH220925757, VN00027, IN00602"
            )
            return WAITING_TICKET_NUMBER

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

    def _is_valid_ticket_number(self, text: str) -> bool:
        """
        Validate if the input text looks like a valid ticket number
        
        Args:
            text: Input text to validate
            
        Returns:
            True if it looks like a ticket number, False otherwise
        """
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