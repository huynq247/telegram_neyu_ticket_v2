"""
Comment message formatters for Telegram UI.
Handles all comment-related message formatting with proper styling.
"""
from typing import List
from datetime import datetime
from ...application.dto import CommentDTO, TicketDTO


class CommentFormatter:
    """Formats comment-related messages for Telegram"""
    
    def __init__(self):
        self.max_content_length = 1000  # Telegram message limit consideration
    
    def format_comments_list(self, ticket: TicketDTO, comments: List[CommentDTO]) -> str:
        """Format list of comments for a ticket"""
        if not comments:
            return self._format_no_comments_message(ticket)
        
        message = f"📝 **Comments for Ticket {ticket.number}**\n"
        message += f"🎫 **Title:** {ticket.title}\n\n"
        
        for i, comment in enumerate(comments, 1):
            message += self._format_single_comment(comment, i)
            message += "\n" + "─" * 40 + "\n\n"
        
        message += f"💬 **Total:** {len(comments)} comment(s)\n"
        message += f"📅 **Last Updated:** {ticket.updated_date.strftime('%Y-%m-%d %H:%M')}"
        
        return message
    
    def format_single_comment(self, comment: CommentDTO, ticket: TicketDTO) -> str:
        """Format a single comment for display"""
        message = f"💬 **Comment on Ticket {ticket.number}**\n\n"
        message += self._format_single_comment(comment, 1)
        message += f"\n🎫 **Ticket:** {ticket.title}"
        
        return message
    
    def format_comment_added_success(self, comment: CommentDTO, ticket: TicketDTO) -> str:
        """Format success message after adding comment"""
        type_text = {
            'public': '💬 Public comment',
            'internal': '🔒 Internal note',
            'system': '🤖 System comment'
        }.get(comment.comment_type, '💬 Comment')
        
        message = f"✅ **{type_text} added successfully!**\n\n"
        message += f"🎫 **Ticket:** {ticket.number} - {ticket.title}\n"
        message += f"📝 **Your comment:**\n{self._truncate_content(comment.content)}\n\n"
        message += f"⏰ **Added at:** {comment.formatted_date}"
        
        return message
    
    def format_recent_tickets_for_comments(self, tickets: List[TicketDTO]) -> str:
        """Format recent tickets list for comment selection"""
        if not tickets:
            return "📋 **No recent tickets found.**\n\nYou don't have any recent tickets to comment on."
        
        message = "📋 **Select a ticket to view/add comments:**\n\n"
        
        for ticket in tickets[:10]:  # Limit to 10 for UI clarity
            message += f"{ticket.status_emoji} **{ticket.number}**\n"
            message += f"📝 {ticket.title[:60]}{'...' if len(ticket.title) > 60 else ''}\n"
            message += f"🏷️ {ticket.priority} • 📅 {ticket.created_date.strftime('%m/%d')}\n\n"
        
        if len(tickets) > 10:
            message += f"... and {len(tickets) - 10} more tickets\n\n"
        
        message += "💡 **Tip:** Type ticket number or select from the keyboard below."
        
        return message
    
    def format_comment_preview(self, comments: List[CommentDTO], ticket: TicketDTO) -> str:
        """Format comment preview (first few comments)"""
        if not comments:
            return self._format_no_comments_message(ticket)
        
        message = f"💬 **Recent Comments - {ticket.number}**\n"
        message += f"🎫 {ticket.title}\n\n"
        
        # Show last 3 comments
        recent_comments = comments[-3:] if len(comments) > 3 else comments
        
        for comment in recent_comments:
            message += f"{comment.type_emoji} **{comment.display_author}** • {comment.formatted_date}\n"
            message += f"💭 {comment.preview_content}\n\n"
        
        if len(comments) > 3:
            message += f"... and {len(comments) - 3} more comment(s)\n\n"
        
        message += "📖 **View All** | ➕ **Add Comment**"
        
        return message
    
    def format_comment_templates(self, templates: List[str]) -> str:
        """Format comment templates for selection"""
        if not templates:
            return "📝 **No templates available**\n\nPlease type your comment manually."
        
        message = "📝 **Quick Comment Templates:**\n\n"
        message += "Select a template to use or type your own comment:\n\n"
        
        for i, template in enumerate(templates[:8], 1):  # Limit to 8 templates
            message += f"{i}️⃣ {template}\n\n"
        
        message += "✏️ **Or type your custom comment below:**"
        
        return message
    
    def format_comment_validation_warning(self, warnings: List[str]) -> str:
        """Format comment validation warnings"""
        if not warnings:
            return ""
        
        message = "⚠️ **Warning before posting:**\n\n"
        
        for warning in warnings:
            message += f"• {warning}\n"
        
        message += "\n❓ **Do you want to post this comment anyway?**"
        
        return message
    
    def format_comment_search_results(self, comments: List[CommentDTO], query: str) -> str:
        """Format comment search results"""
        if not comments:
            return f"🔍 **No comments found for:** '{query}'\n\nTry different keywords or check spelling."
        
        message = f"🔍 **Search Results for:** '{query}'\n"
        message += f"Found {len(comments)} comment(s)\n\n"
        
        for comment in comments[:5]:  # Show top 5 results
            message += f"{comment.type_emoji} **{comment.display_author}** • Ticket {comment.ticket_number}\n"
            message += f"📅 {comment.formatted_date}\n"
            message += f"💭 {comment.preview_content}\n\n"
        
        if len(comments) > 5:
            message += f"... and {len(comments) - 5} more result(s)\n\n"
        
        message += "💡 **Tip:** Tap on a result to view full comment"
        
        return message
    
    def _format_single_comment(self, comment: CommentDTO, index: int) -> str:
        """Format a single comment entry"""
        comment_text = f"**Comment #{index}**\n"
        comment_text += f"{comment.type_emoji} **{comment.display_author}"
        
        if comment.is_edited:
            comment_text += " (edited)"
        
        comment_text += f"**\n📅 {comment.formatted_date}\n\n"
        
        # Truncate long content
        content = self._truncate_content(comment.content)
        comment_text += f"💬 {content}"
        
        if comment.is_recent:
            comment_text += " 🆕"
        
        return comment_text
    
    def _format_no_comments_message(self, ticket: TicketDTO) -> str:
        """Format message when no comments exist"""
        message = f"📝 **Ticket {ticket.number}**\n"
        message += f"🎫 **Title:** {ticket.title}\n\n"
        message += "❌ **No comments found**\n\n"
        message += "💡 Be the first to add a comment!\n"
        message += "Use the button below to start the conversation."
        
        return message
    
    def _truncate_content(self, content: str) -> str:
        """Truncate content if too long"""
        if len(content) <= self.max_content_length:
            return content
        
        return content[:self.max_content_length - 3] + "..."
    
    def format_comment_type_selection(self) -> str:
        """Format comment type selection message"""
        message = "🔖 **Select comment type:**\n\n"
        message += "💬 **Public Comment**\n"
        message += "   • Visible to ticket creator and assignee\n"
        message += "   • Standard communication\n\n"
        message += "🔒 **Internal Note**\n"
        message += "   • Only visible to support team\n"
        message += "   • Private discussion\n\n"
        message += "❓ **Which type would you like to add?**"
        
        return message
    
    def format_thread_view(self, parent_comment: CommentDTO, replies: List[CommentDTO]) -> str:
        """Format threaded comment view"""
        message = f"🧵 **Comment Thread**\n\n"
        message += "**Original Comment:**\n"
        message += self._format_single_comment(parent_comment, 1)
        
        if replies:
            message += f"\n\n**Replies ({len(replies)}):**\n\n"
            for i, reply in enumerate(replies, 1):
                message += f"↳ {self._format_single_comment(reply, i)}\n\n"
        else:
            message += "\n\n**No replies yet**\n"
            message += "💡 Be the first to reply!"
        
        return message