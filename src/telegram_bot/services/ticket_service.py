"""
Ticket Service Module
Xử lý business logic liên quan đến tickets
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TicketService:
    """Service xử lý các thao tác với tickets"""
    
    def __init__(self, ticket_manager):
        self.ticket_manager = ticket_manager
    
    async def create_ticket(self, user_data: Dict[str, Any], destination: str, user_id: int = None, auth_service = None) -> Dict[str, Any]:
        """
        Create new ticket
        
        Args:
            user_data: User data
            destination: Destination
            user_id: Telegram user ID (optional, for getting email)
            auth_service: Auth service (optional, for getting email)
            
        Returns:
            Ticket creation result
        """
        try:
            ticket_data = {
                'title': f"Ticket từ Telegram - {user_data['username']}",
                'description': user_data['description'],
                'telegram_chat_id': str(user_data['chat_id']),
                'priority': user_data['priority']  # Already integer
            }
            
            # Thêm email nếu user đã authenticated
            if user_id and auth_service:
                user_info = auth_service.get_user_info(user_id)
                if user_info and 'email' in user_info:
                    ticket_data['partner_email'] = user_info['email']
                    ticket_data['partner_name'] = user_info.get('name', 'Telegram User')
                    logger.info(f"Adding email {user_info['email']} to ticket")
            
            logger.info(f"Creating ticket with data: {ticket_data} for destination: {destination}")
            result = await self.ticket_manager.create_ticket(ticket_data, destination)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {
                'success': False,
                'message': f'Error occurred while creating ticket: {str(e)}'
            }
    
    async def get_user_tickets(self, user_id: int, auth_service) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tickets của user theo email
        
        Args:
            user_id: Telegram user ID
            auth_service: Authentication service để lấy email
            
        Returns:
            Danh sách tickets
        """
        try:
            # Get user email from auth service
            user_info = auth_service.get_user_info(user_id)
            if not user_info or 'email' not in user_info:
                logger.warning(f"No user info or email found for user {user_id}")
                return []

            user_email = user_info['email']
            logger.info(f"Getting tickets for user_id={user_id}, email={user_email}")
            tickets = await self.ticket_manager.get_user_tickets(user_email)
            logger.info(f"Found {len(tickets)} tickets for email {user_email}")
            return tickets
            
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    def validate_ticket_data(self, user_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate ticket data before creation
        
        Args:
            user_data: User data
            
        Returns:
            (is_valid, error_message)
        """
        from ..utils.validators import BotValidators
        return BotValidators.validate_user_data(user_data)
    
    def get_priority_info(self, callback_data: str) -> tuple[int, str]:
        """
        Lấy thông tin priority từ callback data
        
        Args:
            callback_data: Callback data từ button
            
        Returns:
            (priority_code, priority_text)
        """
        from ..utils.formatters import BotFormatters
        return BotFormatters.PRIORITY_MAP.get(callback_data, (2, '🟡 Trung bình'))
    
    async def get_ticket_detail(self, ticket_id: int) -> Dict[str, Any]:
        """
        Lấy chi tiết ticket
        
        Args:
            ticket_id: ID của ticket
            
        Returns:
            Chi tiết ticket hoặc empty dict nếu không tìm thấy
        """
        try:
            ticket = self.ticket_manager.pg_connector.get_ticket(ticket_id)
            return ticket if ticket else {}
            
        except Exception as e:
            logger.error(f"Error getting ticket detail {ticket_id}: {e}")
            return {}
    
    async def get_filtered_tickets(self, user_id: int, auth_service, status_filter: str = None, priority_filter: int = None) -> List[Dict[str, Any]]:
        """
        Lấy tickets với filter
        
        Args:
            user_id: Telegram user ID
            auth_service: Authentication service để lấy email
            status_filter: Filter theo status ('new', 'in_progress', 'done', 'cancelled')
            priority_filter: Filter theo priority (1=low, 2=normal, 3=high, 4=urgent)
            
        Returns:
            Danh sách tickets đã được filter
        """
        try:
            # Get user email from auth service
            user_info = auth_service.get_user_info(user_id)
            if not user_info or 'email' not in user_info:
                return []
            
            user_email = user_info['email']
            tickets = self.ticket_manager.pg_connector.get_filtered_user_tickets(
                user_email, status_filter, priority_filter
            )
            return tickets
            
        except Exception as e:
            logger.error(f"Error getting filtered tickets: {e}")
            return []
    
    async def search_tickets(self, user_id: int, auth_service, search_term: str) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tickets theo từ khóa
        
        Args:
            user_id: Telegram user ID
            auth_service: Authentication service để lấy email
            search_term: Từ khóa tìm kiếm
            
        Returns:
            Danh sách tickets khớp với từ khóa
        """
        try:
            # Get user email from auth service
            user_info = auth_service.get_user_info(user_id)
            if not user_info or 'email' not in user_info:
                return []
            
            user_email = user_info['email']
            tickets = self.ticket_manager.pg_connector.search_user_tickets(user_email, search_term)
            return tickets
            
        except Exception as e:
            logger.error(f"Error searching tickets: {e}")
            return []
    
    async def get_paginated_tickets(self, user_id: int, auth_service, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
        """
        Lấy tickets với pagination
        
        Args:
            user_id: Telegram user ID
            auth_service: Authentication service để lấy email
            page: Trang hiện tại (1-indexed)
            per_page: Số tickets mỗi trang
            
        Returns:
            Dict chứa tickets, total_count, current_page, total_pages
        """
        try:
            # Get user email from auth service
            user_info = auth_service.get_user_info(user_id)
            if not user_info or 'email' not in user_info:
                return {
                    'tickets': [],
                    'total_count': 0,
                    'current_page': 1,
                    'total_pages': 0
                }
            
            user_email = user_info['email']
            result = self.ticket_manager.pg_connector.get_paginated_user_tickets(
                user_email, page, per_page
            )
            return result
            
        except Exception as e:
            logger.error(f"Error getting paginated tickets: {e}")
            return {
                'tickets': [],
                'total_count': 0,
                'current_page': 1,
                'total_pages': 0
            }