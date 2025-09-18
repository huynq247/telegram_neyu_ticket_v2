"""
PostgreSQL Connector Module
Kết nối trực tiếp với PostgreSQL database thay vì Odoo XML-RPC
"""
import psycopg2
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PostgreSQLConnector:
    """Class để kết nối trực tiếp với PostgreSQL database"""
    
    def __init__(self, host: str, port: int, database: str, username: str, password: str):
        """
        Khởi tạo kết nối PostgreSQL
        
        Args:
            host: Host của PostgreSQL server
            port: Port (15432)
            database: Tên database
            username: Tên đăng nhập
            password: Mật khẩu
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        
        # Kết nối tới PostgreSQL
        self._connect()
    
    def _connect(self) -> None:
        """Kết nối với PostgreSQL server"""
        try:
            connection_string = f"host='{self.host}' port='{self.port}' dbname='{self.database}' user='{self.username}' password='{self.password}'"
            
            self.connection = psycopg2.connect(connection_string)
            self.connection.autocommit = True
            
            logger.info(f"Kết nối PostgreSQL thành công - {self.host}:{self.port}/{self.database}")
            
        except Exception as e:
            logger.error(f"Lỗi kết nối PostgreSQL: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Kiểm tra kết nối với PostgreSQL
        
        Returns:
            True nếu kết nối thành công
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            
            logger.info(f"PostgreSQL version: {version[0]}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi test kết nối PostgreSQL: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """
        Lấy danh sách tables trong database
        
        Returns:
            Danh sách tên tables
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"Found {len(tables)} tables in database")
            return tables
            
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách tables: {e}")
            return []
    
    def find_helpdesk_tables(self) -> List[str]:
        """
        Tìm các tables liên quan đến helpdesk/tickets
        
        Returns:
            Danh sách tables có thể chứa tickets
        """
        try:
            tables = self.list_tables()
            
            # Tìm tables có tên liên quan đến helpdesk, ticket, support
            helpdesk_keywords = ['helpdesk', 'ticket', 'support', 'issue', 'request']
            helpdesk_tables = []
            
            for table in tables:
                for keyword in helpdesk_keywords:
                    if keyword in table.lower():
                        helpdesk_tables.append(table)
                        break
            
            logger.info(f"Found potential helpdesk tables: {helpdesk_tables}")
            return helpdesk_tables
            
        except Exception as e:
            logger.error(f"Lỗi tìm helpdesk tables: {e}")
            return []
    
    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Mô tả cấu trúc của table
        
        Args:
            table_name: Tên table
            
        Returns:
            Danh sách columns với thông tin
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'column_name': row[0],
                    'data_type': row[1],
                    'is_nullable': row[2],
                    'column_default': row[3]
                })
            
            cursor.close()
            logger.info(f"Table {table_name} has {len(columns)} columns")
            return columns
            
        except Exception as e:
            logger.error(f"Lỗi describe table {table_name}: {e}")
            return []
    
    def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo ticket mới trong project_task table (Odoo's task system)
        
        Args:
            ticket_data: Dictionary chứa thông tin ticket
                - title: Tiêu đề ticket
                - description: Mô tả chi tiết
                - telegram_chat_id: ID chat Telegram để tracking
                - priority: Độ ưu tiên (0-3, default 1)
                
        Returns:
            Dictionary chứa kết quả tạo ticket
        """
        try:
            cursor = self.connection.cursor()
            
            # Chuẩn bị dữ liệu ticket với giá trị mặc định phù hợp
            from datetime import datetime
            current_time = datetime.now()
            
            task_data = {
                'name': ticket_data.get('title', 'Support Ticket from Telegram'),
                'description': ticket_data.get('description', ''),
                'state': '01_in_progress',  # State hợp lệ cho ticket mới
                'priority': str(ticket_data.get('priority', 1)),
                'active': True,
                'display_in_project': True,
                'project_id': 1,  # IT Support / Tickets project
                'stage_id': 1,    # To Do stage  
                'create_uid': 1,  # Default user
                'write_uid': 1,   # Default user
                'create_date': current_time,  # Set create date
                'write_date': current_time,   # Set write date
                'x_tracking_id': f"TG_{ticket_data.get('telegram_chat_id', 'unknown')}"
            }
            
            # Tạo INSERT query động
            columns = list(task_data.keys())
            values = list(task_data.values())
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(values))
            
            insert_query = f"""
                INSERT INTO project_task ({columns_str})
                VALUES ({placeholders})
                RETURNING id, name, state;
            """
            
            cursor.execute(insert_query, values)
            result = cursor.fetchone()
            ticket_id, ticket_name, ticket_state = result
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Tạo ticket thành công: ID={ticket_id}, Name={ticket_name}")
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'ticket_name': ticket_name,
                'state': ticket_state,
                'tracking_id': task_data['x_tracking_id'],
                'message': f'Ticket #{ticket_id} đã được tạo thành công'
            }
            
        except Exception as e:
            logger.error(f"Lỗi tạo ticket: {e}")
            if hasattr(self, 'connection'):
                try:
                    self.connection.rollback()
                except:
                    pass
            return {
                'success': False,
                'error': str(e),
                'message': 'Không thể tạo ticket. Vui lòng thử lại.'
            }
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin ticket từ project_task table
        
        Args:
            ticket_id: ID của ticket
            
        Returns:
            Dictionary chứa thông tin ticket hoặc None nếu không tìm thấy
        """
        try:
            cursor = self.connection.cursor()
            
            # Query từ project_task với join để lấy thêm thông tin
            query = """
                SELECT 
                    pt.id,
                    pt.name,
                    pt.description,
                    pt.state,
                    pt.priority,
                    pt.project_id,
                    pt.stage_id,
                    pt.x_tracking_id,
                    pt.create_date,
                    pt.write_date,
                    pp.name as project_name,
                    pps.name as stage_name
                FROM project_task pt
                LEFT JOIN project_project pp ON pt.project_id = pp.id
                LEFT JOIN project_project_stage pps ON pt.stage_id = pps.id
                WHERE pt.id = %s;
            """
            
            cursor.execute(query, (ticket_id,))
            row = cursor.fetchone()
            
            if not row:
                cursor.close()
                return None
            
            # Map kết quả
            ticket_info = {
                'id': row[0],
                'name': row[1],
                'description': row[2] or '',
                'state': row[3],
                'priority': row[4],
                'project_id': row[5],
                'stage_id': row[6],
                'tracking_id': row[7],
                'create_date': row[8],
                'write_date': row[9],
                'project_name': row[10] if isinstance(row[10], str) else (row[10].get('en_US', '') if row[10] else ''),
                'stage_name': row[11] if isinstance(row[11], str) else (row[11].get('en_US', '') if row[11] else '')
            }
            
            cursor.close()
            logger.info(f"Lấy thông tin ticket {ticket_id} thành công")
            return ticket_info
            
        except Exception as e:
            logger.error(f"Lỗi lấy ticket {ticket_id}: {e}")
            return None
    
    def get_completed_tickets(self, telegram_chat_id: str = None) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tickets đã hoàn thành từ project_task
        
        Args:
            telegram_chat_id: Lọc theo chat ID cụ thể (optional)
            
        Returns:
            Danh sách tickets đã hoàn thành
        """
        try:
            cursor = self.connection.cursor()
            
            # Query tickets có stage "Done" (stage_id = 3)
            base_query = """
                SELECT 
                    pt.id,
                    pt.name,
                    pt.description,
                    pt.state,
                    pt.priority,
                    pt.x_tracking_id,
                    pt.create_date,
                    pt.write_date,
                    pps.name as stage_name
                FROM project_task pt
                LEFT JOIN project_project_stage pps ON pt.stage_id = pps.id
                WHERE pt.stage_id = 3  -- Done stage
            """
            
            # Thêm filter theo tracking_id nếu có
            params = []
            if telegram_chat_id:
                base_query += " AND pt.x_tracking_id = %s"
                params.append(f"TG_{telegram_chat_id}")
            
            base_query += " ORDER BY pt.write_date DESC LIMIT 20;"
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'state': row[3],
                    'priority': row[4],
                    'tracking_id': row[5],
                    'create_date': row[6],
                    'write_date': row[7],
                    'stage_name': row[8] if isinstance(row[8], str) else (row[8].get('en_US', '') if row[8] else ''),
                    'telegram_chat_id': row[5].replace('TG_', '') if row[5] and row[5].startswith('TG_') else ''
                }
                tickets.append(ticket_info)
            
            cursor.close()
            logger.info(f"Tìm thấy {len(tickets)} tickets hoàn thành")
            return tickets
            
        except Exception as e:
            logger.error(f"Lỗi lấy completed tickets: {e}")
            return []
    
    def get_user_tickets(self, telegram_chat_id: str) -> List[Dict[str, Any]]:
        """
        Lấy tất cả tickets của một user từ Telegram
        
        Args:
            telegram_chat_id: ID chat Telegram
            
        Returns:
            Danh sách tickets của user
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    pt.id,
                    pt.name,
                    pt.description,
                    pt.state,
                    pt.priority,
                    pt.x_tracking_id,
                    pt.create_date,
                    pt.write_date,
                    pps.name as stage_name
                FROM project_task pt
                LEFT JOIN project_project_stage pps ON pt.stage_id = pps.id
                WHERE pt.x_tracking_id = %s
                ORDER BY pt.create_date DESC
                LIMIT 10;
            """
            
            cursor.execute(query, (f"TG_{telegram_chat_id}",))
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'state': row[3],
                    'priority': row[4],
                    'tracking_id': row[5],
                    'create_date': row[6],
                    'write_date': row[7],
                    'stage_name': row[8] if isinstance(row[8], str) else (row[8].get('en_US', '') if row[8] else 'Unknown')
                }
                tickets.append(ticket_info)
            
            cursor.close()
            logger.info(f"Tìm thấy {len(tickets)} tickets cho user {telegram_chat_id}")
            return tickets
            
        except Exception as e:
            logger.error(f"Lỗi lấy user tickets: {e}")
            return []
    
    def close(self) -> None:
        """Đóng kết nối database"""
        if self.connection:
            self.connection.close()
            logger.info("Đã đóng kết nối PostgreSQL")