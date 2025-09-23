"""
Ticket message formatters for Telegram UI.
Handles all ticket-related message formatting with proper styling.
"""
from typing import List, Optional
from datetime import datetime
from ...application.dto import TicketDTO


class TicketFormatter:
    """Formats ticket-related messages for Telegram"""
    
    def __init__(self):
        self.max_description_length = 200
    
    def format_ticket_list(self, tickets: List[TicketDTO], title: str = "🎫 Your Tickets") -> str:
        """Format list of tickets"""
        if not tickets:
            return f"{title}\n\n❌ No tickets found.\n\n💡 Create your first ticket to get started!"
        
        message = f"{title}\n\n"
        
        for ticket in tickets:
            message += self._format_ticket_summary(ticket)
            message += "\n" + "─" * 30 + "\n\n"
        
        message += f"📊 **Total:** {len(tickets)} ticket(s)"
        
        return message
    
    def format_ticket_details(self, ticket: TicketDTO, comment_count: int = 0) -> str:
        """Format detailed ticket information"""
        message = f"🎫 **Ticket Details**\n\n"
        message += f"**#{ticket.number}** {ticket.status_emoji}\n"
        message += f"📝 **Title:** {ticket.title}\n\n"
        
        # Description
        description = self._truncate_text(ticket.description, self.max_description_length)
        message += f"📄 **Description:**\n{description}\n\n"
        
        # Status and Priority
        message += f"🏷️ **Status:** {ticket.status} {ticket.status_emoji}\n"
        message += f"⚡ **Priority:** {ticket.priority} {ticket.priority_emoji}\n\n"
        
        # People
        message += f"👤 **Created by:** {self._format_email(ticket.creator_email)}\n"
        if ticket.assignee_email:
            message += f"👨‍💼 **Assigned to:** {self._format_email(ticket.assignee_email)}\n"
        else:
            message += f"👨‍💼 **Assigned to:** Unassigned\n"
        
        message += "\n"
        
        # Dates
        message += f"📅 **Created:** {ticket.created_date.strftime('%Y-%m-%d %H:%M')}\n"
        message += f"🔄 **Updated:** {ticket.updated_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        if ticket.resolved_date:
            message += f"✅ **Resolved:** {ticket.resolved_date.strftime('%Y-%m-%d %H:%M')}\n"
        
        # Additional info
        if ticket.is_overdue:
            message += f"\n⚠️ **Status:** OVERDUE\n"
        
        if comment_count > 0:
            message += f"\n💬 **Comments:** {comment_count}\n"
        
        return message
    
    def format_ticket_summary_for_selection(self, tickets: List[TicketDTO]) -> str:
        """Format tickets for selection (shorter format)"""
        if not tickets:
            return "📋 **No tickets available for selection.**"
        
        message = "📋 **Select a ticket:**\n\n"
        
        for ticket in tickets[:10]:  # Limit display
            message += f"{ticket.status_emoji} **{ticket.number}**\n"
            message += f"📝 {ticket.title[:50]}{'...' if len(ticket.title) > 50 else ''}\n"
            message += f"🏷️ {ticket.priority} • 📅 {self._format_relative_date(ticket.created_date)}\n\n"
        
        if len(tickets) > 10:
            message += f"... and {len(tickets) - 10} more tickets\n\n"
        
        message += "💡 **Select a ticket from the options below.**"
        
        return message
    
    def format_ticket_search_results(self, tickets: List[TicketDTO], query: str) -> str:
        """Format search results"""
        if not tickets:
            return f"🔍 **No tickets found for:** '{query}'\n\nTry different keywords or check your spelling."
        
        message = f"🔍 **Search Results for:** '{query}'\n"
        message += f"Found {len(tickets)} ticket(s)\n\n"
        
        for ticket in tickets[:5]:  # Show top 5
            message += self._format_ticket_summary(ticket, compact=True)
            message += "\n"
        
        if len(tickets) > 5:
            message += f"\n... and {len(tickets) - 5} more result(s)\n"
        
        message += "\n💡 **Select a ticket to view details**"
        
        return message
    
    def format_ticket_status_summary(self, status_counts: dict, overdue_count: int = 0) -> str:
        """Format ticket status summary"""
        message = "📊 **Your Ticket Summary**\n\n"
        
        if not status_counts:
            message += "❌ No tickets found.\n\n💡 Create your first ticket!"
            return message
        
        # Status breakdown
        status_emojis = {
            'Open': '🟢',
            'In Progress': '🟡',
            'Resolved': '🔵',
            'Closed': '⚫'
        }
        
        total = sum(status_counts.values())
        
        for status, count in status_counts.items():
            if count > 0:
                emoji = status_emojis.get(status, '❓')
                percentage = (count / total * 100) if total > 0 else 0
                message += f"{emoji} **{status}:** {count} ({percentage:.0f}%)\n"
        
        message += f"\n📈 **Total Tickets:** {total}\n"
        
        if overdue_count > 0:
            message += f"⚠️ **Overdue:** {overdue_count}\n"
        
        return message
    
    def format_ticket_filters(self, current_status: Optional[str] = None, current_priority: Optional[str] = None) -> str:
        """Format current filter information"""
        message = "🔍 **Current Filters:**\n\n"
        
        if current_status:
            message += f"📊 **Status:** {current_status}\n"
        else:
            message += f"📊 **Status:** All\n"
        
        if current_priority:
            message += f"⚡ **Priority:** {current_priority}\n"
        else:
            message += f"⚡ **Priority:** All\n"
        
        message += "\n💡 **Use the buttons below to change filters.**"
        
        return message
    
    def format_recent_activity(self, tickets: List[TicketDTO]) -> str:
        """Format recent ticket activity"""
        if not tickets:
            return "📊 **Recent Activity**\n\n❌ No recent activity."
        
        message = "📊 **Recent Activity**\n\n"
        
        for ticket in tickets[:5]:
            days_ago = (datetime.now() - ticket.updated_date).days
            
            if days_ago == 0:
                time_text = "Today"
            elif days_ago == 1:
                time_text = "Yesterday"
            else:
                time_text = f"{days_ago} days ago"
            
            message += f"{ticket.status_emoji} **{ticket.number}** - {time_text}\n"
            message += f"   {ticket.title[:40]}{'...' if len(ticket.title) > 40 else ''}\n\n"
        
        return message
    
    def _format_ticket_summary(self, ticket: TicketDTO, compact: bool = False) -> str:
        """Format a single ticket summary"""
        summary = f"{ticket.status_emoji} **{ticket.number}** - {ticket.priority_emoji}\n"
        summary += f"📝 **{ticket.title}**\n"
        
        if not compact:
            description = self._truncate_text(ticket.description, 100)
            summary += f"💬 {description}\n"
        
        summary += f"👤 {self._format_email(ticket.creator_email)} • "
        summary += f"📅 {self._format_relative_date(ticket.created_date)}\n"
        
        if ticket.is_overdue:
            summary += "⚠️ **OVERDUE**\n"
        
        return summary
    
    def _format_email(self, email: str) -> str:
        """Format email for display (show name part only)"""
        if not email or '@' not in email:
            return email or 'Unknown'
        
        return email.split('@')[0].replace('.', ' ').title()
    
    def _format_relative_date(self, date: datetime) -> str:
        """Format date relative to now"""
        now = datetime.now()
        diff = now - date
        
        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks}w ago"
        else:
            return date.strftime('%m/%d/%Y')
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis"""
        if not text:
            return "No description"
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - 3] + "..."