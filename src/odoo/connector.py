"""
Odoo Connector Module
Kết nối và tương tác với API Odoo để quản lý tickets
"""
import xmlrpc.client
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OdooConnector:
    """Class để kết nối và tương tác với Odoo API"""
    
    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Khởi tạo kết nối Odoo
        
        Args:
            url: URL của server Odoo
            db: Tên database
            username: Tên đăng nhập
            password: Mật khẩu
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None
        
        # Kết nối tới Odoo
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Xác thực với Odoo server"""
        try:
            # Kết nối tới common endpoint
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # Lấy thông tin version
            version_info = common.version()
            logger.info(f"Kết nối Odoo thành công. Version: {version_info}")
            
            # Xác thực người dùng
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if not self.uid:
                raise Exception("Xác thực Odoo thất bại")
            
            # Kết nối tới models endpoint
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            logger.info(f"Xác thực Odoo thành công. UID: {self.uid}")
            
        except Exception as e:
            logger.error(f"Lỗi kết nối Odoo: {e}")
            raise
    
    def create_ticket(self, ticket_data: Dict[str, Any]) -> int:
        """
        Tạo ticket mới trong Odoo
        
        Args:
            ticket_data: Dữ liệu ticket
            
        Returns:
            ID của ticket được tạo
        """
        try:
            # Chuẩn bị dữ liệu ticket cho Odoo
            odoo_data = {
                'name': ticket_data.get('subject', 'Ticket từ Telegram'),
                'description': ticket_data.get('description', ''),
                'partner_name': ticket_data.get('customer_name', 'Khách hàng Telegram'),
                'email_from': ticket_data.get('customer_email', ''),
                'team_id': ticket_data.get('team_id', 1),  # Default team
                'priority': ticket_data.get('priority', '2'),  # Normal priority
                'stage_id': 1,  # New stage
                'user_id': ticket_data.get('assigned_user', False),
                'create_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'telegram_chat_id': ticket_data.get('telegram_chat_id', ''),
                'telegram_user_id': ticket_data.get('telegram_user_id', ''),
            }
            
            # Tạo ticket trong Odoo helpdesk
            ticket_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'helpdesk.ticket', 'create', [odoo_data]
            )
            
            logger.info(f"Tạo ticket thành công trong Odoo. ID: {ticket_id}")
            return ticket_id
            
        except Exception as e:
            logger.error(f"Lỗi tạo ticket trong Odoo: {e}")
            raise
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin ticket từ Odoo
        
        Args:
            ticket_id: ID của ticket
            
        Returns:
            Thông tin ticket hoặc None nếu không tìm thấy
        """
        try:
            tickets = self.models.execute_kw(
                self.db, self.uid, self.password,
                'helpdesk.ticket', 'read', 
                [ticket_id], 
                {'fields': ['name', 'description', 'stage_id', 'partner_name', 
                           'email_from', 'priority', 'user_id', 'create_date',
                           'write_date', 'telegram_chat_id', 'telegram_user_id']}
            )
            
            if tickets:
                return tickets[0]
            return None
            
        except Exception as e:
            logger.error(f"Lỗi lấy thông tin ticket {ticket_id}: {e}")
            return None
    
    def update_ticket(self, ticket_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Cập nhật ticket trong Odoo
        
        Args:
            ticket_id: ID của ticket
            update_data: Dữ liệu cập nhật
            
        Returns:
            True nếu cập nhật thành công
        """
        try:
            result = self.models.execute_kw(
                self.db, self.uid, self.password,
                'helpdesk.ticket', 'write',
                [ticket_id, update_data]
            )
            
            logger.info(f"Cập nhật ticket {ticket_id} thành công")
            return result
            
        except Exception as e:
            logger.error(f"Lỗi cập nhật ticket {ticket_id}: {e}")
            return False
    
    def get_completed_tickets(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tickets đã hoàn thành
        
        Returns:
            Danh sách tickets đã hoàn thành
        """
        try:
            # Tìm tickets có stage_id là "Done"
            ticket_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'helpdesk.ticket', 'search',
                [[['stage_id.name', '=', 'Done'], 
                  ['telegram_chat_id', '!=', False]]]
            )
            
            if not ticket_ids:
                return []
            
            tickets = self.models.execute_kw(
                self.db, self.uid, self.password,
                'helpdesk.ticket', 'read',
                [ticket_ids],
                {'fields': ['name', 'description', 'stage_id', 'partner_name',
                           'telegram_chat_id', 'telegram_user_id', 'write_date']}
            )
            
            return tickets
            
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách tickets hoàn thành: {e}")
            return []
    
    def search_tickets(self, domain: List = None) -> List[int]:
        """
        Tìm kiếm tickets theo điều kiện
        
        Args:
            domain: Điều kiện tìm kiếm Odoo
            
        Returns:
            Danh sách ID tickets
        """
        try:
            if domain is None:
                domain = []
            
            ticket_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'helpdesk.ticket', 'search', [domain]
            )
            
            return ticket_ids
            
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm tickets: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Kiểm tra kết nối với Odoo
        
        Returns:
            True nếu kết nối thành công
        """
        try:
            # Thử lấy thông tin user hiện tại
            user_info = self.models.execute_kw(
                self.db, self.uid, self.password,
                'res.users', 'read', [self.uid], 
                {'fields': ['name', 'login']}
            )
            
            if user_info:
                logger.info(f"Kết nối Odoo OK. User: {user_info[0]['name']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Lỗi test kết nối Odoo: {e}")
            return False