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
    
    async def create_ticket(self, user_data: Dict[str, Any], destination: str) -> Dict[str, Any]:
        """
        Tạo ticket mới
        
        Args:
            user_data: Dữ liệu user
            destination: Điểm đến
            
        Returns:
            Kết quả tạo ticket
        """
        try:
            ticket_data = {
                'title': f"Ticket từ Telegram - {user_data['username']}",
                'description': user_data['description'],
                'telegram_chat_id': str(user_data['chat_id']),
                'priority': user_data['priority']  # Already integer
            }
            
            logger.info(f"Creating ticket with data: {ticket_data} for destination: {destination}")
            result = await self.ticket_manager.create_ticket(ticket_data, destination)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {
                'success': False,
                'message': f'Có lỗi xảy ra khi tạo ticket: {str(e)}'
            }
    
    async def get_user_tickets(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tickets của user
        
        Args:
            chat_id: ID chat của user
            
        Returns:
            Danh sách tickets
        """
        try:
            tickets = await self.ticket_manager.get_user_tickets(chat_id)
            return tickets
            
        except Exception as e:
            logger.error(f"Error getting user tickets: {e}")
            return []
    
    def validate_ticket_data(self, user_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate dữ liệu ticket trước khi tạo
        
        Args:
            user_data: Dữ liệu user
            
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