"""
Awaiting Tickets Handler Module

This module handles all awaiting ticket operations including:
- Displaying awaiting tickets (filtered by "Waiting" status)
- Mark ticket as done functionality
- Add comments to awaiting tickets
- Deep link commands for awaiting tickets
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from .base_view_handler import BaseViewHandler, VIEWING_AWAITING, WAITING_AWAITING_COMMENT, VIEWING_LIST

logger = logging.getLogger(__name__)


class AwaitingTicketsHandler(BaseViewHandler):
    """Handler for awaiting ticket operations"""
    
    def __init__(self, ticket_service, auth_service, keyboards):
        """Initialize awaiting tickets handler"""
        super().__init__(ticket_service, auth_service, keyboards=keyboards)
        self.keyboards = keyboards

    async def handle_awaiting_tickets(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle view awaiting tickets callback"""
        query = update.callback_query
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
                return VIEWING_LIST
            
            # Format awaiting tickets message
            message = self._format_awaiting_tickets_message(awaiting_tickets)
            keyboard = self.keyboards.get_awaiting_tickets_keyboard(awaiting_tickets)
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            return VIEWING_AWAITING
            
        except Exception as e:
            logger.error(f"Error viewing awaiting tickets for user {user_id}: {e}")
            await query.edit_message_text(
                "❌ Error loading awaiting tickets. Please try again.",
                reply_markup=self.keyboards.get_back_to_tickets_keyboard()
            )
            return VIEWING_LIST

    async def handle_awaiting_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle add comment for awaiting ticket"""
        query = update.callback_query
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
            
            return WAITING_AWAITING_COMMENT
            
        except Exception as e:
            logger.error(f"Error initiating comment for awaiting ticket: {e}")
            await query.edit_message_text(
                "❌ Error processing request. Please try again.",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
            )
            return VIEWING_AWAITING

    async def handle_awaiting_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle mark done for awaiting ticket"""
        query = update.callback_query
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
            
            return VIEWING_AWAITING
            
        except Exception as e:
            logger.error(f"Error marking awaiting ticket as done: {e}")
            await query.edit_message_text(
                "❌ Error processing request. Please try again.",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
            )
            return VIEWING_AWAITING

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
                return VIEWING_AWAITING
            
            if not comment_text:
                await update.message.reply_text(
                    "❌ Comment cannot be empty. Please enter a valid comment or use 'Back to Awaiting' button to cancel:",
                    reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
                )
                return WAITING_AWAITING_COMMENT
            
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
            
            return VIEWING_AWAITING
            
        except Exception as e:
            logger.error(f"Error adding comment to awaiting ticket: {e}")
            await update.message.reply_text(
                "❌ Error adding comment. Please try again.",
                reply_markup=self.keyboards.get_back_to_awaiting_keyboard()
            )
            return VIEWING_AWAITING

    async def handle_awaiting_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle click on ticket info (just answer the callback)"""
        query = update.callback_query
        await query.answer("ℹ️ Ticket information displayed above")
        return VIEWING_AWAITING

    async def handle_separator(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle click on separator (just answer the callback)"""
        query = update.callback_query
        return VIEWING_AWAITING

    # Deep link command handlers
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

    def _format_awaiting_tickets_message(self, awaiting_tickets: list) -> str:
        """Format awaiting tickets message"""
        message = "⏳ <b>Your Awaiting Tickets</b>\n\n"
        
        # Show count info
        if len(awaiting_tickets) > 10:
            message += f"📊 Found {len(awaiting_tickets)} awaiting tickets (showing first 10)\n"
        else:
            message += f"📊 Found {len(awaiting_tickets)} awaiting tickets\n"
        
        message += f"\n💡 <b>Use the buttons below to take action on each ticket.</b>\n\n"
        
        # Add instruction text as regular text - only for Mark Done section
        message += "📝 <b>Confirm to close tickets (Mark as Done):</b>\n\n"
        message += f"🎯 <b>Click on the underlined links above to take action on tickets.</b>"
        
        return message