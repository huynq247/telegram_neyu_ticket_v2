"""
Base View Handler Module
Chứa các constants, states và base functionality chung cho view ticket handlers
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Conversation states
VIEWING_LIST, VIEWING_DETAIL, SEARCHING, FILTERING, VIEWING_COMMENTS, WAITING_TICKET_NUMBER, WAITING_ADD_COMMENT_TICKET, WAITING_COMMENT_TEXT, VIEWING_AWAITING, WAITING_AWAITING_COMMENT = range(10)

class BaseViewHandler:
    """Base class cho các view ticket handlers"""
    
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
    
    def __init__(self, ticket_service, auth_service, formatters=None, keyboards=None):
        """
        Initialize BaseViewHandler
        
        Args:
            ticket_service: Instance của TicketService
            auth_service: Instance của AuthService
            formatters: Instance của BotFormatters (optional)
            keyboards: Instance của BotKeyboards (optional)
        """
        self.ticket_service = ticket_service
        self.auth_service = auth_service
        self.formatters = formatters
        self.keyboards = keyboards
        
        # Store user states
        self.user_states = {}
    
    def _is_authenticated(self, user_id: int) -> bool:
        """Check if user is authenticated"""
        return self.auth_service.is_authenticated(user_id)
    
    def _get_user_state(self, user_id: int) -> Dict[str, Any]:
        """Get or create user state"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                'current_page': 1,
                'search_term': None,
                'filter_type': None,
                'filter_value': None
            }
        return self.user_states[user_id]
    
    def _reset_user_state(self, user_id: int):
        """Reset user state to default"""
        self.user_states[user_id] = {
            'current_page': 1,
            'search_term': None,
            'filter_type': None,
            'filter_value': None
        }