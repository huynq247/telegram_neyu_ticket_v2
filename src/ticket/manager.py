"""
Ticket Manager Module
Quản lý luồng ticket giữa Telegram và Odoo
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.telegram_bot.utils.smart_logging import get_smart_logger
    logger = get_smart_logger(__name__)
except ImportError:
    # Fallback to regular logger if smart_logging not available
    logger = logging.getLogger(__name__)

class TicketManager:
    """Class quản lý tickets giữa Telegram và Odoo"""
    
    def __init__(self, postgresql_connector, telegram_handler=None):
        """
        Khởi tạo TicketManager
        
        Args:
            postgresql_connector: Instance của PostgreSQLConnector
            telegram_handler: Instance của TelegramBotHandler (optional)
        """
        self.pg_connector = postgresql_connector
        self.telegram_handler = telegram_handler
        
        # Cache để theo dõi tickets đã thông báo
        self.notified_tickets = set()
        
        # Task cho việc kiểm tra tickets hoàn thành
        self.check_task = None
    
    async def create_ticket(self, ticket_data: Dict[str, Any], destination: str = "Vietnam") -> Dict[str, Any]:
        """
        Tạo ticket mới trong PostgreSQL với multi-destination support
        
        Args:
            ticket_data: Dictionary chứa thông tin ticket
                - title: Tiêu đề ticket
                - description: Mô tả chi tiết
                - telegram_chat_id: ID chat Telegram
                - priority: Độ ưu tiên (0-3)
            destination: Điểm đến (Vietnam, Thailand, India, Singapore)
            
        Returns:
            Dictionary chứa kết quả tạo ticket
        """
        try:
            # Validate dữ liệu đầu vào
            if not self._validate_ticket_data(ticket_data):
                return {
                    'success': False,
                    'message': 'Dữ liệu ticket không hợp lệ'
                }
            
            # Tạo ticket trong PostgreSQL với destination
            result = self.pg_connector.create_ticket(ticket_data, destination)
            
            if result['success']:
                ticket_number = result.get('ticket_number', f"#{result['ticket_id']}")
                logger.info(f"TicketManager: Tạo {destination} ticket {ticket_number} thành công")
            else:
                logger.error(f"TicketManager: Lỗi tạo {destination} ticket - {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"TicketManager: Exception tạo ticket - {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Có lỗi xảy ra khi tạo ticket'
            }
    
    def _validate_ticket_data(self, ticket_data: Dict[str, Any]) -> bool:
        """
        Validate dữ liệu ticket
        
        Args:
            ticket_data: Dữ liệu ticket cần validate
            
        Returns:
            True nếu dữ liệu hợp lệ
        """
        # Required fields cho PostgreSQL
        required_fields = ['title', 'description', 'telegram_chat_id']
        
        for field in required_fields:
            if not ticket_data.get(field):
                logger.error(f"TicketManager: Thiếu field bắt buộc: {field}")
                return False
        
        # Validate title length
        title = ticket_data.get('title', '')
        if len(title.strip()) < 3:
            logger.error("TicketManager: Title quá ngắn (tối thiểu 3 ký tự)")
            return False
        
        # Validate priority
        priority = ticket_data.get('priority', 1)
        if not isinstance(priority, int) or priority not in [0, 1, 2, 3]:
            logger.error(f"TicketManager: Priority không hợp lệ: {priority}")
            return False
        
        return True
    
    async def get_user_tickets(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tickets của user từ PostgreSQL theo email
        
        Args:
            user_email: Email của user đã đăng nhập
            
        Returns:
            Danh sách tickets của user
        """
        try:
            # Lấy tickets từ PostgreSQL
            tickets = self.pg_connector.get_user_tickets(user_email)
            
            logger.info(f"TicketManager: Lấy {len(tickets)} tickets cho user {user_email}")
            return tickets
            
        except Exception as e:
            logger.error(f"TicketManager: Lỗi lấy tickets user {user_email} - {e}")
            return []
    
    async def update_ticket(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Cập nhật ticket
        
        Args:
            ticket_id: ID ticket
            update_data: Dữ liệu cập nhật
            
        Returns:
            True nếu cập nhật thành công
        """
        try:
            result = self.odoo_connector.update_ticket(ticket_id, update_data)
            
            if result:
                logger.info(f"TicketManager: Cập nhật ticket {ticket_id} thành công")
            else:
                logger.error(f"TicketManager: Cập nhật ticket {ticket_id} thất bại")
            
            return result
            
        except Exception as e:
            logger.error(f"TicketManager: Lỗi cập nhật ticket {ticket_id} - {e}")
            return False
    
    async def check_completed_tickets(self) -> None:
        """Kiểm tra và thông báo tickets hoàn thành từ PostgreSQL"""
        try:
            # Lấy danh sách tickets hoàn thành
            completed_tickets = self.pg_connector.get_completed_tickets()
            
            if not completed_tickets:
                # Sử dụng throttled logging để tránh spam
                if hasattr(logger, 'debug_throttled'):
                    logger.debug_throttled("TicketManager: Không có tickets hoàn thành mới", interval=600)  # 10 minutes
                else:
                    logger.debug("TicketManager: Không có tickets hoàn thành mới")
                return
            
            # Filter tickets: chỉ giữ lại tickets có chat_id hợp lệ
            valid_tickets = []
            for ticket in completed_tickets:
                tracking_id = ticket.get('tracking_id', '')
                chat_id = tracking_id.replace('TG_', '') if tracking_id.startswith('TG_') else None
                
                # Chỉ thêm vào danh sách nếu có chat_id hợp lệ
                if chat_id and chat_id != 'unknown':
                    valid_tickets.append(ticket)
            
            # Nếu không có tickets hợp lệ nào, return luôn
            if not valid_tickets:
                logger.debug("TicketManager: Không có tickets hoàn thành với chat_id hợp lệ")
                return
            
            # Thông báo cho từng ticket chưa được thông báo
            for ticket in valid_tickets:
                ticket_id = ticket['id']
                
                # Bỏ qua nếu đã thông báo rồi
                if ticket_id in self.notified_tickets:
                    continue
                
                # Lấy chat_id từ tracking_id (đã validate ở trên)
                tracking_id = ticket.get('tracking_id', '')
                chat_id = tracking_id.replace('TG_', '')
                
                # Gửi thông báo qua Telegram
                if self.telegram_handler:
                    success = await self.telegram_handler.send_ticket_completion_notification(
                        chat_id, ticket
                    )
                    
                    if success:
                        # Đánh dấu đã thông báo
                        self.notified_tickets.add(ticket_id)
                        logger.info(f"TicketManager: Đã thông báo hoàn thành ticket {ticket_id}")
                    else:
                        logger.error(f"TicketManager: Lỗi gửi thông báo ticket {ticket_id}")
                else:
                    logger.warning("TicketManager: Không có telegram_handler để gửi thông báo")
            
        except Exception as e:
            logger.error(f"TicketManager: Lỗi kiểm tra tickets hoàn thành - {e}")
    
    async def start_monitoring(self, check_interval: int = 60) -> None:
        """
        Bắt đầu giám sát tickets hoàn thành
        
        Args:
            check_interval: Khoảng thời gian kiểm tra (giây)
        """
        logger.info(f"TicketManager: Bắt đầu giám sát tickets (interval: {check_interval}s)")
        
        while True:
            try:
                await self.check_completed_tickets()
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                logger.info("TicketManager: Dừng giám sát tickets")
                break
            except Exception as e:
                logger.error(f"TicketManager: Lỗi trong quá trình giám sát - {e}")
                await asyncio.sleep(check_interval)
    
    def start_monitoring_task(self, check_interval: int = 60) -> None:
        """
        Khởi tạo task giám sát tickets
        
        Args:
            check_interval: Khoảng thời gian kiểm tra (giây)
        """
        if self.check_task and not self.check_task.done():
            logger.warning("TicketManager: Task giám sát đã đang chạy")
            return
        
        self.check_task = asyncio.create_task(self.start_monitoring(check_interval))
        logger.info("TicketManager: Đã khởi tạo task giám sát tickets")
    
    def stop_monitoring_task(self) -> None:
        """Dừng task giám sát tickets"""
        if self.check_task and not self.check_task.done():
            self.check_task.cancel()
            logger.info("TicketManager: Đã dừng task giám sát tickets")
    
    async def get_ticket_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê tickets
        
        Returns:
            Dictionary chứa thống kê tickets
        """
        try:
            stats = {
                'total_tickets': 0,
                'new_tickets': 0,
                'in_progress_tickets': 0,
                'completed_tickets': 0,
                'high_priority_tickets': 0,
                'telegram_tickets': 0
            }
            
            # Tổng số tickets
            all_ticket_ids = self.odoo_connector.search_tickets([])
            stats['total_tickets'] = len(all_ticket_ids)
            
            # Tickets từ Telegram
            telegram_ticket_ids = self.odoo_connector.search_tickets([
                ['telegram_chat_id', '!=', False]
            ])
            stats['telegram_tickets'] = len(telegram_ticket_ids)
            
            # Tickets hoàn thành
            completed_ticket_ids = self.odoo_connector.search_tickets([
                ['stage_id.name', '=', 'Done']
            ])
            stats['completed_tickets'] = len(completed_ticket_ids)
            
            # Tickets ưu tiên cao
            high_priority_ids = self.odoo_connector.search_tickets([
                ['priority', '=', '3']
            ])
            stats['high_priority_tickets'] = len(high_priority_ids)
            
            logger.info(f"TicketManager: Thống kê tickets - {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"TicketManager: Lỗi lấy thống kê tickets - {e}")
            return {}
    
    def set_telegram_handler(self, telegram_handler) -> None:
        """
        Thiết lập telegram handler
        
        Args:
            telegram_handler: Instance của TelegramBotHandler
        """
        self.telegram_handler = telegram_handler
        logger.info("TicketManager: Đã thiết lập telegram handler")
    
    async def cleanup_old_notifications(self, days: int = 7) -> None:
        """
        Dọn dẹp cache thông báo cũ
        
        Args:
            days: Số ngày để giữ lại cache
        """
        try:
            # Trong thực tế, bạn có thể lưu timestamp của notifications
            # và dọn dẹp dựa trên thời gian
            
            # Hiện tại chỉ clear cache nếu quá lớn
            if len(self.notified_tickets) > 1000:
                self.notified_tickets.clear()
                logger.info("TicketManager: Đã dọn dẹp cache notifications")
                
        except Exception as e:
            logger.error(f"TicketManager: Lỗi dọn dẹp cache - {e}")
    
    def __del__(self):
        """Destructor để dừng task khi object bị xóa"""
        if hasattr(self, 'check_task') and self.check_task and not self.check_task.done():
            self.check_task.cancel()