"""
PostgreSQL Connector Module
Kết nối trực tiếp với PostgreSQL database thay vì Odoo XML-RPC
Multi-Destination Support: Vietnam, Thailand, India, Singapore
"""
import psycopg2
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# Import country configuration
try:
    from ..config.country_config import get_country_config, get_supported_countries
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
    from country_config import get_country_config, get_supported_countries

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

    def test_helpdesk_ticket_access(self) -> Dict[str, Any]:
        """
        Test quyền truy cập vào bảng helpdesk_ticket
        
        Returns:
            Dictionary chứa kết quả test
        """
        try:
            cursor = self.connection.cursor()
            
            # Test read access
            cursor.execute("SELECT COUNT(*) FROM helpdesk_ticket;")
            count = cursor.fetchone()[0]
            
            # Get latest Vietnam tickets
            cursor.execute("""
                SELECT id, number, name, description, create_date 
                FROM helpdesk_ticket 
                WHERE name LIKE '%TKVN%' OR number LIKE 'HT%'
                ORDER BY id DESC 
                LIMIT 5;
            """)
            vietnam_tickets = cursor.fetchall()
            
            cursor.close()
            
            return {
                'success': True,
                'has_read_access': True,
                'record_count': count,
                'vietnam_tickets': vietnam_tickets,
                'message': f'Có quyền truy cập helpdesk_ticket với {count} records, {len(vietnam_tickets)} Vietnam tickets'
            }
            
        except Exception as e:
            return {
                'success': False,
                'has_read_access': False,
                'error': str(e),
                'message': f'Lỗi truy cập helpdesk_ticket: {e}'
            }

    def generate_vietnam_ticket_number(self) -> str:
        """
        Tạo số ticket HT theo format hiện tại
        
        Returns:
            Ticket number theo format HT00XXX
        """
        try:
            cursor = self.connection.cursor()
            
            # Lấy HT number cao nhất
            cursor.execute("""
                SELECT number 
                FROM helpdesk_ticket 
                WHERE number LIKE 'HT%' 
                ORDER BY CAST(SUBSTRING(number FROM 3) AS INTEGER) DESC 
                LIMIT 1;
            """)
            
            latest_record = cursor.fetchone()
            
            if latest_record and latest_record[0]:
                # Extract number from "HT00012"
                import re
                match = re.search(r'HT(\d+)', latest_record[0])
                if match:
                    latest_number = int(match.group(1))
                    next_number = latest_number + 1
                    ticket_number = f"HT{str(next_number).zfill(5)}"
                else:
                    ticket_number = "HT00013"
            else:
                # Start from HT00001
                ticket_number = "HT00001"
            
            cursor.close()
            logger.info(f"Generated Vietnam Ticket number: {ticket_number}")
            return ticket_number
            
        except Exception as e:
            logger.error(f"Lỗi tạo Vietnam ticket number: {e}")
            # Fallback
            import random
            return f"HT{str(random.randint(13, 99)).zfill(5)}"
    
    def generate_ticket_number(self, country: str, table_name: str = None) -> str:
        """
        Tạo số ticket theo quốc gia (Multi-destination support)
        
        Args:
            country: Tên quốc gia (Vietnam, Thailand, India, etc.)
            table_name: Tên bảng (optional, sẽ lấy từ config)
            
        Returns:
            Ticket number theo format [COUNTRY_CODE]00XXX (VN00001, TH00001, etc.)
        """
        try:
            # Load country config with fallback
            try:
                from ..config.country_config import get_country_config
            except ImportError:
                # Inline config as fallback
                COUNTRY_CONFIG = {
                    'Vietnam': {'code': 'VN', 'table': 'helpdesk_ticket', 'prefix': 'VN'},
                    'Thailand': {'code': 'TH', 'table': 'helpdesk_ticket_thailand', 'prefix': 'TH'},
                    'India': {'code': 'IN', 'table': 'helpdesk_ticket_india', 'prefix': 'IN'},
                    'Singapore': {'code': 'SG', 'table': 'helpdesk_ticket_singapore', 'prefix': 'SG'}
                }
                
                def get_country_config(country_name):
                    if country_name not in COUNTRY_CONFIG:
                        raise ValueError(f"Quốc gia '{country_name}' không được hỗ trợ")
                    return COUNTRY_CONFIG[country_name]
            
            config = get_country_config(country)
            prefix = config['prefix']
            target_table = table_name or config['table']
            
            cursor = self.connection.cursor()
            
            # Lấy ticket number cao nhất cho country này
            cursor.execute(f"""
                SELECT number 
                FROM {target_table}
                WHERE number LIKE '{prefix}%' 
                ORDER BY CAST(SUBSTRING(number FROM 3) AS INTEGER) DESC 
                LIMIT 1;
            """)
            
            latest_record = cursor.fetchone()
            
            if latest_record and latest_record[0]:
                # Extract number từ "VN00012", "TH00005", etc.
                import re
                match = re.search(f'{prefix}(\\d+)', latest_record[0])
                if match:
                    latest_number = int(match.group(1))
                    next_number = latest_number + 1
                    ticket_number = f"{prefix}{str(next_number).zfill(5)}"
                else:
                    ticket_number = f"{prefix}00001"
            else:
                # Start from [PREFIX]00001
                ticket_number = f"{prefix}00001"
            
            cursor.close()
            logger.info(f"Generated {country} Ticket number: {ticket_number}")
            return ticket_number
            
        except Exception as e:
            logger.error(f"Lỗi tạo {country} ticket number: {e}")
            # Fallback - generate random number
            import random
            fallback_prefix = country[:2].upper() if len(country) >= 2 else "XX"
            return f"{fallback_prefix}{str(random.randint(1, 999)).zfill(5)}"
    
    def create_ticket(self, ticket_data: Dict[str, Any], destination: str = "Vietnam") -> Dict[str, Any]:
        """
        Tạo ticket mới cho điểm đến được chỉ định (Multi-destination support)
        
        Args:
            ticket_data: Dictionary chứa thông tin ticket
                - title: Tiêu đề ticket  
                - description: Mô tả chi tiết
                - telegram_chat_id: ID chat Telegram để tracking
                - priority: Độ ưu tiên (0-3, default 1)
            destination: Điểm đến (Vietnam, Thailand, India, Singapore)
                
        Returns:
            Dictionary chứa kết quả tạo ticket
        """
        try:
            # Load country configuration with fallback
            try:
                from ..config.country_config import get_country_config
            except ImportError:
                # Inline config as fallback
                COUNTRY_CONFIG = {
                    'Vietnam': {
                        'code': 'VN', 'table': 'helpdesk_ticket', 'prefix': 'VN',
                        'name_template': 'From Telegram Vietnam',
                        'description_template': 'Ticket từ Vietnam cho user request. {description}',
                        'team_id': 1, 'stage_id': 1
                    },
                    'Thailand': {
                        'code': 'TH', 'table': 'helpdesk_ticket_thailand', 'prefix': 'TH',
                        'name_template': 'From Telegram Thailand',
                        'description_template': 'Ticket từ Thailand cho user request. {description}',
                        'team_id': 2, 'stage_id': 1
                    },
                    'India': {
                        'code': 'IN', 'table': 'helpdesk_ticket_india', 'prefix': 'IN',
                        'name_template': 'From Telegram India',
                        'description_template': 'Ticket từ India cho user request. {description}',
                        'team_id': 3, 'stage_id': 1
                    },
                    'Singapore': {
                        'code': 'SG', 'table': 'helpdesk_ticket_singapore', 'prefix': 'SG',
                        'name_template': 'From Telegram Singapore',
                        'description_template': 'Ticket từ Singapore cho user request. {description}',
                        'team_id': 4, 'stage_id': 1
                    }
                }
                
                def get_country_config(country_name):
                    if country_name not in COUNTRY_CONFIG:
                        raise ValueError(f"Quốc gia '{country_name}' không được hỗ trợ")
                    return COUNTRY_CONFIG[country_name]
            
            # Get destination configuration
            config = get_country_config(destination)
            
            cursor = self.connection.cursor()
            
            # Generate ticket number cho destination này
            ticket_number = self.generate_ticket_number(destination, config['table'])
            
            # Chuẩn bị dữ liệu theo config của destination
            current_time = datetime.now()
            
            # Format description theo template của destination
            user_description = ticket_data.get("description", f"User request from {destination}")
            description_text = config['description_template'].format(description=user_description)
            description_html = f'<div data-oe-version="1.2">{description_text}</div>'
            
            # Tạo data structure cho ticket
            helpdesk_data = {
                'number': ticket_number,  # VN00001, TH00001, etc.
                'name': config['name_template'],  # From Telegram Vietnam, etc.
                'description': description_html,
                'priority': str(ticket_data.get('priority', '1')),
                'stage_id': config['stage_id'],  # Stage cho destination
                'team_id': config['team_id'],    # Team cho destination
                'company_id': 1,  # Required field
                'create_uid': 1,  # Default user
                'write_uid': 1,   # Default user
                'create_date': current_time,
                'write_date': current_time,
                'active': True,
                'unattended': True,
                'sequence': 10
            }
            
            # Thêm thông tin partner nếu có
            if 'partner_email' in ticket_data:
                helpdesk_data['partner_email'] = ticket_data['partner_email']
                logger.info(f"Adding partner_email: {ticket_data['partner_email']}")
            
            if 'partner_name' in ticket_data:
                helpdesk_data['partner_name'] = ticket_data['partner_name']
            
            # Tạo INSERT query cho table của destination
            table_name = config['table']
            columns = list(helpdesk_data.keys())
            values = list(helpdesk_data.values())
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(values))
            
            # Kiểm tra xem table có tồn tại không (fallback về helpdesk_ticket)
            try:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1;")
            except Exception:
                logger.warning(f"Table {table_name} không tồn tại, fallback về helpdesk_ticket")
                table_name = 'helpdesk_ticket'
            
            insert_query = f"""
                INSERT INTO {table_name} ({columns_str})
                VALUES ({placeholders})
                RETURNING id, number, name;
            """
            
            cursor.execute(insert_query, values)
            result = cursor.fetchone()
            ticket_id, returned_number, ticket_name = result
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Tạo {destination} Ticket thành công: ID={ticket_id}, Number={returned_number}, Name={ticket_name}")
            
            return {
                'success': True,
                'ticket_id': ticket_id,
                'ticket_number': returned_number,
                'ticket_name': ticket_name,
                'destination': destination,
                'destination_code': config['code'],
                'ticket_full_id': f"{returned_number} - {ticket_name}",
                'state': 'created',
                'message': f'{destination} Ticket {returned_number} - {ticket_name} (#{ticket_id}) đã được tạo thành công'
            }
            
        except Exception as e:
            logger.error(f"Lỗi tạo {destination} ticket: {e}")
            if hasattr(self, 'connection'):
                try:
                    self.connection.rollback()
                except:
                    pass
            return {
                'success': False,
                'error': str(e),
                'destination': destination,
                'message': f'Không thể tạo {destination} ticket. Vui lòng thử lại.'
            }
    
    # Destination-specific wrapper methods for easy access
    def create_vietnam_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo Vietnam ticket (VN00XXX - From Telegram Vietnam)"""
        return self.create_ticket(ticket_data, "Vietnam")
    
    def create_thailand_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo Thailand ticket (TH00XXX - From Telegram Thailand)"""
        return self.create_ticket(ticket_data, "Thailand")
    
    def create_india_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo India ticket (IN00XXX - From Telegram India)"""
        return self.create_ticket(ticket_data, "India")
    
    def create_philippines_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo Philippines ticket (PH00XXX - From Telegram Philippines)"""
        return self.create_ticket(ticket_data, "Philippines")
    
    def create_malaysia_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo Malaysia ticket (MY00XXX - From Telegram Malaysia)"""
        return self.create_ticket(ticket_data, "Malaysia")
    
    def create_indonesia_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo Indonesia ticket (ID00XXX - From Telegram Indonesia)"""
        return self.create_ticket(ticket_data, "Indonesia")
    
    def get_supported_destinations(self) -> List[str]:
        """Trả về danh sách các destination được hỗ trợ"""
        try:
            from ..config.country_config import get_supported_countries
            return get_supported_countries()
        except ImportError:
            return ['Vietnam', 'Thailand', 'India', 'Philippines', 'Malaysia', 'Indonesia']
    
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
    
    def get_user_tickets(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Lấy tất cả tickets của một user theo email
        
        Args:
            user_email: Email của user đã đăng nhập
            
        Returns:
            Danh sách tickets của user
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    ht.id,
                    ht.name,
                    ht.description,
                    'draft' as state,
                    ht.priority,
                    ht.number as tracking_id,
                    ht.create_date,
                    ht.write_date,
                    'Open' as stage_name
                FROM helpdesk_ticket ht
                WHERE ht.partner_email = %s OR ht.partner_email ILIKE %s
                ORDER BY ht.create_date DESC
                LIMIT 10;
            """
            
            cursor.execute(query, (user_email, f"%{user_email}%"))
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
            logger.info(f"Tìm thấy {len(tickets)} tickets cho user {user_email}")
            return tickets
            
        except Exception as e:
            logger.error(f"Lỗi lấy user tickets: {e}")
            return []
    
    def get_filtered_user_tickets(self, user_email: str, status_filter: str = None, priority_filter: int = None) -> List[Dict[str, Any]]:
        """
        Lấy tickets của user với filter
        
        Args:
            user_email: Email của user đã đăng nhập
            status_filter: Filter theo status
            priority_filter: Filter theo priority
            
        Returns:
            Danh sách tickets được filter
        """
        try:
            cursor = self.connection.cursor()
            
            # Base query
            query = """
                SELECT 
                    ht.id,
                    ht.name,
                    ht.description,
                    'draft' as state,
                    ht.priority,
                    ht.number as tracking_id,
                    ht.create_date,
                    ht.write_date,
                    'Open' as stage_name
                FROM helpdesk_ticket ht
                WHERE (ht.partner_email = %s OR ht.partner_email ILIKE %s)
            """
            
            params = [user_email, f"%{user_email}%"]
            
            # Add filters
            if status_filter:
                # Since we don't have stage table, just ignore status filter for now
                pass
            
            if priority_filter:
                query += " AND ht.priority = %s"
                params.append(str(priority_filter))
            
            query += " ORDER BY ht.create_date DESC LIMIT 20;"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'state': row[3],
                    'priority': row[4],
                    'tracking_id': row[5],
                    'create_date': row[6].strftime('%Y-%m-%d %H:%M') if row[6] else 'N/A',
                    'write_date': row[7].strftime('%Y-%m-%d %H:%M') if row[7] else 'N/A',
                    'stage_name': row[8] if isinstance(row[8], str) else (row[8].get('en_US', '') if row[8] else 'Unknown')
                }
                tickets.append(ticket_info)
            
            cursor.close()
            return tickets
            
        except Exception as e:
            logger.error(f"Lỗi lấy filtered tickets: {e}")
            return []
    
    def search_user_tickets(self, user_email: str, search_term: str) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tickets của user theo từ khóa
        
        Args:
            user_email: Email của user đã đăng nhập
            search_term: Từ khóa tìm kiếm
            
        Returns:
            Danh sách tickets khớp với từ khóa
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
                SELECT 
                    ht.id,
                    ht.name,
                    ht.description,
                    'draft' as state,
                    ht.priority,
                    ht.number as tracking_id,
                    ht.create_date,
                    ht.write_date,
                    'Open' as stage_name
                FROM helpdesk_ticket ht
                WHERE (ht.partner_email = %s OR ht.partner_email ILIKE %s)
                AND (ht.name ILIKE %s OR ht.description ILIKE %s)
                ORDER BY ht.create_date DESC
                LIMIT 15;
            """
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (user_email, f"%{user_email}%", search_pattern, search_pattern))
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'state': row[3],
                    'priority': row[4],
                    'tracking_id': row[5],
                    'create_date': row[6].strftime('%Y-%m-%d %H:%M') if row[6] else 'N/A',
                    'write_date': row[7].strftime('%Y-%m-%d %H:%M') if row[7] else 'N/A',
                    'stage_name': row[8] if isinstance(row[8], str) else (row[8].get('en_US', '') if row[8] else 'Unknown')
                }
                tickets.append(ticket_info)
            
            cursor.close()
            return tickets
            
        except Exception as e:
            logger.error(f"Lỗi search tickets: {e}")
            return []
    
    def get_paginated_user_tickets(self, user_email: str, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
        """
        Lấy tickets với pagination
        
        Args:
            user_email: Email của user đã đăng nhập
            page: Trang hiện tại (1-indexed)
            per_page: Số tickets mỗi trang
            
        Returns:
            Dict chứa tickets và thông tin pagination
        """
        try:
            cursor = self.connection.cursor()
            
            # Count total tickets
            count_query = """
                SELECT COUNT(*) 
                FROM helpdesk_ticket ht
                WHERE ht.partner_email = %s OR ht.partner_email ILIKE %s
            """
            cursor.execute(count_query, (user_email, f"%{user_email}%"))
            total_count = cursor.fetchone()[0]
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Get tickets for current page
            query = """
                SELECT 
                    ht.id,
                    ht.name,
                    ht.description,
                    'draft' as state,
                    ht.priority,
                    ht.number as tracking_id,
                    ht.create_date,
                    ht.write_date,
                    'Open' as stage_name
                FROM helpdesk_ticket ht
                WHERE ht.partner_email = %s OR ht.partner_email ILIKE %s
                ORDER BY ht.create_date DESC
                LIMIT %s OFFSET %s;
            """
            
            cursor.execute(query, (user_email, f"%{user_email}%", per_page, offset))
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'state': row[3],
                    'priority': row[4],
                    'tracking_id': row[5],
                    'create_date': row[6].strftime('%Y-%m-%d %H:%M') if row[6] else 'N/A',
                    'write_date': row[7].strftime('%Y-%m-%d %H:%M') if row[7] else 'N/A',
                    'stage_name': row[8] if isinstance(row[8], str) else (row[8].get('en_US', '') if row[8] else 'Unknown')
                }
                tickets.append(ticket_info)
            
            cursor.close()
            
            return {
                'tickets': tickets,
                'total_count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'per_page': per_page
            }
            
        except Exception as e:
            logger.error(f"Lỗi get paginated tickets: {e}")
            return {
                'tickets': [],
                'total_count': 0,
                'current_page': 1,
                'total_pages': 0,
                'per_page': per_page
            }
    
    def close(self) -> None:
        """Đóng kết nối database"""
        if self.connection:
            self.connection.close()
            logger.info("Đã đóng kết nối PostgreSQL")