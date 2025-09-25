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
        Create new ticket with user type classification
        
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
                'telegram_username': user_data.get('username', ''),
                'priority': user_data['priority']
            }
            
            # Add user authentication info if available
            user_type = None
            auth_method = None
            
            if user_id and auth_service:
                user_info = auth_service.get_user_info(user_id)
                if user_info and 'email' in user_info:
                    ticket_data['partner_email'] = user_info['email']
                    
                    # Handle case where 'name' field is actually an email address
                    user_name = user_info.get('name', 'Telegram User')
                    if '@' in user_name:
                        # If name contains @, it's likely an email - extract proper name
                        display_name = user_name.split('@')[0].replace('.', ' ').replace('_', ' ').title()
                        ticket_data['partner_name'] = display_name
                        logger.info(f"Extracted partner name '{display_name}' from email-like name field '{user_name}'")
                    else:
                        # Use name as-is if it doesn't look like an email
                        ticket_data['partner_name'] = user_name
                    
                    # Extract user type and auth method
                    user_type = user_info.get('user_type', 'portal_user')
                    auth_method = user_info.get('auth_method', 'unknown')
                    
                    logger.info(f"Adding email {user_info['email']} to ticket with user_type={user_type}, auth_method={auth_method}")
            
            # Add user classification for database tracking
            ticket_data['user_type'] = user_type or 'unauthenticated'
            ticket_data['auth_method'] = auth_method or 'none'
            ticket_data['created_via'] = 'telegram_bot'
            
            # Different handling based on user type
            if user_type == 'portal_user':
                # Portal users get special treatment
                ticket_data['source'] = 'telegram_portal_user'
                ticket_data['auto_assign'] = False  # Don't auto-assign portal user tickets
                ticket_data['requires_approval'] = True  # Portal user tickets need approval
                logger.info(f"Creating portal user ticket with special handling")
            elif user_type == 'admin_helpdesk':
                # Admin/helpdesk users get normal treatment
                ticket_data['source'] = 'telegram_admin'
                ticket_data['auto_assign'] = True
                ticket_data['requires_approval'] = False
                logger.info(f"Creating admin/helpdesk user ticket with normal handling")
            else:
                # Unauthenticated users
                ticket_data['source'] = 'telegram_anonymous'
                ticket_data['auto_assign'] = True
                ticket_data['requires_approval'] = False
                logger.info(f"Creating unauthenticated user ticket")
            
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

    async def get_ticket_comments_by_number(self, ticket_number: str) -> List[Dict[str, Any]]:
        """
        Get comments for a ticket by ticket number
        
        Args:
            ticket_number: Ticket tracking number (e.g., TH220925757)
            
        Returns:
            List of comments
        """
        try:
            # Use postgresql_connector to get comments
            comments = await self.ticket_manager.pg_connector.get_ticket_comments_by_number(ticket_number)
            logger.info(f"Retrieved {len(comments)} comments for ticket {ticket_number}")
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments for ticket {ticket_number}: {e}")
            return []

    async def add_comment_to_ticket(self, ticket_number: str, comment_text: str, user_id: int, auth_service) -> bool:
        """
        Add a comment to a ticket
        
        Args:
            ticket_number: Ticket number (e.g., VN00026)
            comment_text: Comment content
            user_id: User ID who is adding the comment
            auth_service: Auth service to get user info
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user email from auth service for author info
            user_info = auth_service.get_user_info(user_id)
            if not user_info or 'email' not in user_info:
                logger.error(f"Could not get user info for user_id {user_id}")
                return False
            
            user_email = user_info['email']
            
            # Add comment to database
            success = await self.ticket_manager.pg_connector.add_comment_to_ticket(
                ticket_number, comment_text, user_email
            )
            
            if success:
                logger.info(f"Comment added successfully to ticket {ticket_number} by {user_email}")
                return True
            else:
                logger.error(f"Failed to add comment to ticket {ticket_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding comment to ticket {ticket_number}: {e}")
            return False

    async def get_recent_tickets(self, user_id: int, auth_service, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent tickets for the user
        
        Args:
            user_id: Telegram user ID
            auth_service: Auth service to get user info
            limit: Number of tickets to return (default 10)
            
        Returns:
            List of recent tickets with basic info
        """
        try:
            # Get user email from auth service
            user_info = auth_service.get_user_info(user_id)
            if not user_info or 'email' not in user_info:
                logger.error(f"Could not get user info for user_id {user_id}")
                return []
            
            user_email = user_info['email']
            
            # Get recent tickets from database (sync call)
            tickets = self.ticket_manager.pg_connector.get_recent_tickets_by_email(user_email, limit)
            logger.info(f"Retrieved {len(tickets)} recent tickets for user {user_email}")
            return tickets
            
        except Exception as e:
            logger.error(f"Error getting recent tickets for user {user_id}: {e}")
            return []

    async def update_ticket_status(self, ticket_number: str, new_status: str) -> bool:
        """
        Update ticket status
        
        Args:
            ticket_number: Ticket number (e.g., TH230925353)
            new_status: New status to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating ticket {ticket_number} to status {new_status}")
            
            # Use ticket manager to update status
            success = await self.ticket_manager.pg_connector.update_ticket_status(
                ticket_number,
                new_status
            )
            
            if success:
                logger.info(f"Successfully updated ticket {ticket_number} to status {new_status}")
            else:
                logger.error(f"Failed to update ticket {ticket_number} to status {new_status}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating ticket status for {ticket_number}: {e}")
            return False

    async def add_comment(self, ticket_number: str, user_id: int, comment_text: str) -> bool:
        """
        Add comment to ticket (wrapper for existing method)
        
        Args:
            ticket_number: Ticket number
            user_id: Telegram user ID
            comment_text: Comment text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.add_comment_to_ticket(ticket_number, comment_text, user_id, self.auth_service)
        except Exception as e:
            logger.error(f"Error in add_comment wrapper: {e}")
            return False