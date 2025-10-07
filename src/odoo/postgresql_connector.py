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
    
    def get_stage_name(self, stage_id: int) -> str:
        """
        Map stage_id to stage name
        
        Args:
            stage_id: ID of the stage
            
        Returns:
            Stage name string
        """
        stage_mapping = {
            1: "New",
            2: "In Progress", 
            3: "Waiting",
            4: "Done",
            5: "Cancelled"
        }
        return stage_mapping.get(stage_id, "Unknown")
    
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
        Tạo số ticket VN theo format mới
        
        Returns:
            Ticket number theo format VN[DDMMYY][XXX] (VN220925001)
        """
        try:
            # Use the new format for Vietnam tickets
            return self.generate_ticket_number("Vietnam")
            
        except Exception as e:
            logger.error(f"Lỗi tạo Vietnam ticket number: {e}")
            # Fallback with new format
            from datetime import datetime
            import random
            date_part = datetime.now().strftime('%d%m%y')
            return f"VN{date_part}{str(random.randint(1, 999)).zfill(3)}"
    
    def generate_ticket_number(self, country: str, table_name: str = None) -> str:
        """
        Tạo số ticket theo quốc gia (Multi-destination support)
        
        Args:
            country: Tên quốc gia (Vietnam, Thailand, India, etc.)
            table_name: Tên bảng (optional, sẽ lấy từ config)
            
        Returns:
            Ticket number theo format [COUNTRY_CODE][DDMMYY][XXX] (VN22092501, TH22092502, etc.)
        """
        try:
            # Load country config with fallback
            try:
                from ..config.country_config import get_country_config
            except ImportError:
                # Inline config as fallback - UPDATED to include all countries
                COUNTRY_CONFIG = {
                    'Vietnam': {'code': 'VN', 'table': 'helpdesk_ticket', 'prefix': 'VN'},
                    'Thailand': {'code': 'TH', 'table': 'helpdesk_ticket_thailand', 'prefix': 'TH'},
                    'India': {'code': 'IN', 'table': 'helpdesk_ticket_india', 'prefix': 'IN'},
                    'Singapore': {'code': 'SG', 'table': 'helpdesk_ticket_singapore', 'prefix': 'SG'},
                    'Philippines': {'code': 'PH', 'table': 'helpdesk_ticket_philippines', 'prefix': 'PH'},
                    'Malaysia': {'code': 'MY', 'table': 'helpdesk_ticket_malaysia', 'prefix': 'MY'},
                    'Indonesia': {'code': 'ID', 'table': 'helpdesk_ticket_indonesia', 'prefix': 'ID'}
                }
                
                def get_country_config(country_name):
                    if country_name not in COUNTRY_CONFIG:
                        raise ValueError(f"Quốc gia '{country_name}' không được hỗ trợ")
                    return COUNTRY_CONFIG[country_name]
            
            config = get_country_config(country)
            prefix = config['prefix']
            target_table = table_name or config['table']
            
            # Generate date part DDMMYY
            from datetime import datetime
            now = datetime.now()
            date_part = now.strftime('%d%m%y')  # Format: DDMMYY (22/09/25 -> 220925)
            
            # Generate unique ticket number with microsecond precision to avoid collisions
            import time
            import random
            
            # Use microsecond timestamp + random number for uniqueness
            microsecond = int(time.time() * 1000000) % 1000  # Last 3 digits of microseconds
            random_part = random.randint(0, 99)  # Random 2 digits
            
            # Combine to create unique 3-digit sequence
            unique_sequence = (microsecond + random_part) % 1000
            if unique_sequence == 0:
                unique_sequence = 1
                
            today_prefix = f"{prefix}{date_part}"
            ticket_number = f"{today_prefix}{str(unique_sequence).zfill(3)}"
            
            # Fallback: if somehow still collision, add more randomness
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {target_table} WHERE number = %s", (ticket_number,))
            if cursor.fetchone()[0] > 0:
                # Collision detected, use random number
                random_seq = random.randint(100, 999)
                ticket_number = f"{today_prefix}{random_seq}"
            
            cursor.close()
            logger.info(f"Generated {country} Ticket number: {ticket_number}")
            return ticket_number
            
        except Exception as e:
            logger.error(f"Lỗi tạo {country} ticket number: {e}")
            # Fallback - generate random number with CORRECT prefix from config
            import random
            from datetime import datetime
            
            # Use the correct prefix from config, not country name
            try:
                # Try to get correct prefix from config
                try:
                    from ..config.country_config import get_country_config
                except ImportError:
                    # Inline config as fallback
                    COUNTRY_CONFIG = {
                        'Vietnam': {'code': 'VN', 'table': 'helpdesk_ticket', 'prefix': 'VN'},
                        'Thailand': {'code': 'TH', 'table': 'helpdesk_ticket_thailand', 'prefix': 'TH'},
                        'India': {'code': 'IN', 'table': 'helpdesk_ticket_india', 'prefix': 'IN'},
                        'Singapore': {'code': 'SG', 'table': 'helpdesk_ticket_singapore', 'prefix': 'SG'},
                        'Philippines': {'code': 'PH', 'table': 'helpdesk_ticket_philippines', 'prefix': 'PH'},
                        'Malaysia': {'code': 'MY', 'table': 'helpdesk_ticket_malaysia', 'prefix': 'MY'},
                        'Indonesia': {'code': 'ID', 'table': 'helpdesk_ticket_indonesia', 'prefix': 'ID'}
                    }
                    
                    def get_country_config(country_name):
                        if country_name not in COUNTRY_CONFIG:
                            raise ValueError(f"Quốc gia '{country_name}' không được hỗ trợ")
                        return COUNTRY_CONFIG[country_name]
                
                config = get_country_config(country)
                fallback_prefix = config['prefix']
            except:
                # Last resort fallback
                fallback_prefix = country[:2].upper() if len(country) >= 2 else "XX"
            
            date_part = datetime.now().strftime('%d%m%y')
            return f"{fallback_prefix}{date_part}{str(random.randint(1, 999)).zfill(3)}"
    
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
                # Inline config as fallback - COMPLETE with all countries
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
                    },
                    'Philippines': {
                        'code': 'PH', 'table': 'helpdesk_ticket_philippines', 'prefix': 'PH',
                        'name_template': 'From Telegram Philippines',
                        'description_template': 'Ticket từ Philippines cho user request. {description}',
                        'team_id': 4, 'stage_id': 1
                    },
                    'Malaysia': {
                        'code': 'MY', 'table': 'helpdesk_ticket_malaysia', 'prefix': 'MY',
                        'name_template': 'From Telegram Malaysia',
                        'description_template': 'Ticket từ Malaysia cho user request. {description}',
                        'team_id': 5, 'stage_id': 1
                    },
                    'Indonesia': {
                        'code': 'ID', 'table': 'helpdesk_ticket_indonesia', 'prefix': 'ID',
                        'name_template': 'From Telegram Indonesia',
                        'description_template': 'Ticket từ Indonesia cho user request. {description}',
                        'team_id': 6, 'stage_id': 1
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
            # Build ticket name: [User Title] - [Destination] - [User Identifier]
            # Priority: Use custom title if provided, otherwise use default template
            user_title = ticket_data.get('title', '').strip()
            telegram_username = ticket_data.get('telegram_username', '').strip()
            
            if telegram_username and telegram_username != 'None' and telegram_username != '':
                user_identifier = f"user:@{telegram_username}"
            else:
                # Fallback: sử dụng authenticated email hoặc unknown
                user_email = ticket_data.get('partner_email') or ticket_data.get('email', 'unknown@email.com')
                user_identifier = user_email
            
            # Format ticket name
            if user_title:
                # Custom title provided: "[Title] - [Destination] - [user:@username]"
                ticket_name_with_identifier = f"{user_title} - {destination} - {user_identifier}"
            else:
                # No title: use default template "From Telegram [Destination] - [user:@username]"
                ticket_name_with_identifier = f"{config['name_template']} - {user_identifier}"
            
            helpdesk_data = {
                'number': ticket_number,  # VN00001, TH00001, etc.
                'name': ticket_name_with_identifier,  # From Telegram Vietnam - user:@Leo2479 or user@email.com
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
            
            # Add user type tracking fields if available
            user_type = ticket_data.get('user_type')
            auth_method = ticket_data.get('auth_method')
            source = ticket_data.get('source')
            
            if user_type:
                # Store user type information in description or additional_info field
                additional_info = {
                    'user_type': user_type,
                    'auth_method': auth_method,
                    'source': source,
                    'created_via': ticket_data.get('created_via', 'telegram_bot'),
                    'requires_approval': ticket_data.get('requires_approval', False),
                    'auto_assign': ticket_data.get('auto_assign', True)
                }
                
                # Try to add to additional_info field if it exists, otherwise add to description
                try:
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'helpdesk_ticket' AND column_name = 'additional_info'")
                    if cursor.fetchone():
                        import json
                        helpdesk_data['additional_info'] = json.dumps(additional_info)
                    else:
                        # Append to description if no additional_info field
                        user_type_info = f"<!-- User Type: {user_type}, Auth: {auth_method}, Source: {source} -->"
                        helpdesk_data['description'] = description_html + user_type_info
                except Exception as e:
                    logger.warning(f"Could not check additional_info field: {e}")
                    # Fallback: append to description
                    user_type_info = f"<!-- User Type: {user_type}, Auth: {auth_method}, Source: {source} -->"
                    helpdesk_data['description'] = description_html + user_type_info
                
                logger.info(f"Added user type tracking: {user_type} via {auth_method} from {source}")
                
                # Handle portal user special requirements
                if user_type == 'portal_user':
                    # Portal users might need different stage or special handling
                    if ticket_data.get('requires_approval'):
                        # Set to a "pending approval" stage if it exists
                        # For now, keep default stage but log the requirement
                        logger.info(f"Portal user ticket {ticket_number} requires approval")
                    
                    if not ticket_data.get('auto_assign', True):
                        # Don't auto-assign to any user - keep user_id as None
                        logger.info(f"Portal user ticket {ticket_number} will not be auto-assigned")
            
            # Handle partner/contact information with special processing for portal users
            partner_email = ticket_data.get('partner_email')
            partner_name = ticket_data.get('partner_name')
            user_type = ticket_data.get('user_type')
            
            if partner_email:
                helpdesk_data['partner_email'] = partner_email
                logger.info(f"Adding partner_email: {partner_email}")
                
                # Always try to find and link existing partner by email (regardless of user_type)
                cursor.execute("""
                    SELECT id, name FROM res_partner 
                    WHERE email = %s AND active = true
                """, (partner_email,))
                
                existing_partner = cursor.fetchone()
                if existing_partner:
                    partner_id, partner_full_name = existing_partner
                    
                    # Link to existing partner
                    helpdesk_data['partner_id'] = partner_id
                    helpdesk_data['commercial_partner_id'] = partner_id
                    helpdesk_data['partner_name'] = partner_name or partner_full_name
                    
                    logger.info(f"Ticket linked to existing partner ID {partner_id} ({partner_full_name}) for {user_type or 'unknown'} user")
                else:
                    # Partner doesn't exist - still set email/name for reference
                    helpdesk_data['partner_name'] = partner_name or partner_email
                    logger.info(f"Ticket created with email reference for {user_type or 'unknown'} user (no existing partner found)")
                    
                    # Note: In production, you might want to create a new partner here
                    # or handle this case differently based on business rules
            
            elif user_type == 'portal_user':
                # Portal user but no email provided - this shouldn't happen but handle gracefully
                logger.warning(f"Portal user ticket created without partner email - this may indicate an authentication issue")
            
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
        Lấy thông tin ticket từ helpdesk_ticket table
        
        Args:
            ticket_id: ID của ticket
            
        Returns:
            Dictionary chứa thông tin ticket hoặc None nếu không tìm thấy
        """
        try:
            cursor = self.connection.cursor()
            
            # Query từ helpdesk_ticket với join để lấy thêm thông tin
            query = """
                SELECT 
                    ht.id,
                    ht.name,
                    ht.description,
                    ht.priority,
                    ht.team_id,
                    ht.stage_id,
                    ht.create_date,
                    ht.write_date,
                    htt.name as team_name,
                    hts.name as stage_name
                FROM helpdesk_ticket ht
                LEFT JOIN helpdesk_ticket_team htt ON ht.team_id = htt.id
                LEFT JOIN helpdesk_ticket_stage hts ON ht.stage_id = hts.id
                WHERE ht.id = %s;
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
                'priority': row[3],
                'team_id': row[4],
                'stage_id': row[5],
                'create_date': row[6],
                'write_date': row[7],
                'team_name': row[8] if isinstance(row[8], str) else (row[8].get('en_US', '') if row[8] else ''),
                'stage_name': row[9] if isinstance(row[9], str) else (row[9].get('en_US', '') if row[9] else '')
            }
            
            cursor.close()
            logger.info(f"Lấy thông tin ticket {ticket_id} thành công")
            return ticket_info
            
        except Exception as e:
            logger.error(f"Lỗi lấy ticket {ticket_id}: {e}")
            return None
    
    def get_completed_tickets(self, telegram_chat_id: str = None) -> List[Dict[str, Any]]:
        """
        Lấy danh sách tickets đã hoàn thành từ helpdesk_ticket
        
        Args:
            telegram_chat_id: Lọc theo chat ID cụ thể (optional)
            
        Returns:
            Danh sách tickets đã hoàn thành
        """
        try:
            cursor = self.connection.cursor()
            
            # Query tickets có stage "Done" hoặc "Solved" (cần check stage nào là done)
            # Tạm thời return empty list vì cần implement logic phù hợp với helpdesk
            base_query = """
                SELECT 
                    ht.id,
                    ht.name,
                    ht.description,
                    ht.priority,
                    ht.create_date,
                    ht.write_date,
                    hts.name as stage_name,
                    htt.name as team_name
                FROM helpdesk_ticket ht
                LEFT JOIN helpdesk_ticket_stage hts ON ht.stage_id = hts.id
                LEFT JOIN helpdesk_ticket_team htt ON ht.team_id = htt.id
                WHERE ht.stage_id IN (
                    SELECT id FROM helpdesk_ticket_stage 
                    WHERE LOWER(name::text) LIKE '%done%' 
                       OR LOWER(name::text) LIKE '%solved%' 
                       OR LOWER(name::text) LIKE '%closed%'
                )
            """
            
            base_query += " ORDER BY ht.write_date DESC LIMIT 20;"
            
            cursor.execute(base_query)
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2] or '',
                    'priority': row[3],
                    'create_date': row[4],
                    'write_date': row[5],
                    'stage_name': row[6] if isinstance(row[6], str) else (row[6].get('en_US', '') if row[6] else ''),
                    'team_name': row[7] if isinstance(row[7], str) else (row[7].get('en_US', '') if row[7] else '')
                }
                tickets.append(ticket_info)
            
            cursor.close()
            # Chỉ log khi có tickets hoàn thành để tránh spam logs
            if len(tickets) > 0:
                logger.info(f"Tìm thấy {len(tickets)} tickets hoàn thành")
            else:
                logger.debug(f"Không có tickets hoàn thành mới")
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
                    ht.stage_id
                FROM helpdesk_ticket ht
                WHERE (ht.partner_email = %s OR ht.partner_email ILIKE %s)
                    AND ht.stage_id != 4
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
                    'stage_name': self.get_stage_name(row[8]) if row[8] else 'Unknown'
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
                    ht.stage_id
                FROM helpdesk_ticket ht
                WHERE (ht.partner_email = %s OR ht.partner_email ILIKE %s)
                    AND ht.stage_id != 4
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
                    'stage_name': self.get_stage_name(row[8]) if row[8] else 'Unknown'
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
                    ht.stage_id
                FROM helpdesk_ticket ht
                WHERE (ht.partner_email = %s OR ht.partner_email ILIKE %s)
                AND (ht.name ILIKE %s OR ht.description ILIKE %s)
                AND ht.stage_id != 4
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
                    'stage_name': self.get_stage_name(row[8]) if row[8] else 'Unknown'
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
            
            # Count total tickets (limit to max 20 most recent, exclude Done status)
            count_query = """
                SELECT COUNT(*) FROM (
                    SELECT ht.id 
                    FROM helpdesk_ticket ht
                    WHERE (ht.partner_email = %s OR ht.partner_email ILIKE %s)
                        AND ht.stage_id != 4
                    ORDER BY ht.create_date DESC
                    LIMIT 20
                ) as limited_tickets
            """
            cursor.execute(count_query, (user_email, f"%{user_email}%"))
            total_count = cursor.fetchone()[0]
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Get tickets for current page (from max 20 most recent, exclude Done status)
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
                    ht.stage_id
                FROM (
                    SELECT * FROM helpdesk_ticket ht2
                    WHERE (ht2.partner_email = %s OR ht2.partner_email ILIKE %s)
                        AND ht2.stage_id != 4
                    ORDER BY ht2.create_date DESC
                    LIMIT 20
                ) ht
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
                    'stage_name': self.get_stage_name(row[8]) if row[8] else 'Unknown'
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
    
    async def get_ticket_comments_by_number(self, ticket_number: str) -> List[Dict[str, Any]]:
        """
        Get comments for a ticket by tracking number
        
        Args:
            ticket_number: Ticket tracking number (e.g., TH220925757)
            
        Returns:
            List of comments
        """
        try:
            cursor = self.connection.cursor()
            
            # First, find the ticket by tracking number
            ticket_query = """
                SELECT id, name 
                FROM helpdesk_ticket 
                WHERE number = %s
                LIMIT 1
            """
            cursor.execute(ticket_query, (ticket_number,))
            ticket = cursor.fetchone()
            
            if not ticket:
                logger.info(f"No ticket found with number: {ticket_number}")
                return []
            
            ticket_id = ticket[0]
            ticket_name = ticket[1]
            
            # Get comments (messages) for this ticket
            comments_query = """
                SELECT 
                    mm.id,
                    mm.body,
                    mm.create_date,
                    mm.author_id,
                    COALESCE(rp.name, rp.email, ru.login, 'Unknown') as author_name,
                    mm.message_type,
                    mm.subtype_id
                FROM mail_message mm
                LEFT JOIN res_partner rp ON mm.author_id = rp.id
                LEFT JOIN res_users ru ON rp.id = ru.partner_id
                WHERE mm.res_id = %s 
                    AND mm.model = 'helpdesk.ticket'
                    AND mm.message_type = 'comment'
                ORDER BY mm.create_date ASC
            """
            
            cursor.execute(comments_query, (ticket_id,))
            rows = cursor.fetchall()
            
            comments = []
            for row in rows:
                comment = {
                    'id': row[0],
                    'body': row[1] or 'No content',
                    'create_date': row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else 'Unknown date',
                    'author_id': row[3],
                    'author_name': row[4] or 'Unknown',
                    'message_type': row[5],
                    'subtype_id': row[6]
                }
                comments.append(comment)
            
            cursor.close()
            logger.info(f"Found {len(comments)} comments for ticket {ticket_number} (ID: {ticket_id})")
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments for ticket {ticket_number}: {e}")
            return []

    async def add_comment_to_ticket(self, ticket_number: str, comment_text: str, user_email: str) -> bool:
        """
        Add a comment to a ticket
        
        Args:
            ticket_number: Ticket number (e.g., VN00026)
            comment_text: Comment content
            user_email: Email of user adding the comment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            
            # First get the ticket ID from the ticket number
            ticket_query = """
            SELECT id FROM helpdesk_ticket 
            WHERE number = %s
            """
            
            cursor.execute(ticket_query, (ticket_number,))
            ticket_result = cursor.fetchone()
            
            if not ticket_result:
                logger.error(f"Ticket not found: {ticket_number}")
                return False
            
            ticket_id = ticket_result[0]
            
            # Get partner_id from user email
            partner_query = """
            SELECT id FROM res_partner 
            WHERE email = %s OR email ILIKE %s
            LIMIT 1
            """
            
            cursor.execute(partner_query, (user_email, f"%{user_email}%"))
            partner_result = cursor.fetchone()
            author_id = partner_result[0] if partner_result else None
            
            # Insert comment into mail_message table
            # This follows Odoo's structure for ticket comments
            insert_comment_query = """
            INSERT INTO mail_message (
                model, res_id, body, message_type, subtype_id, 
                author_id, email_from, create_date, write_date
            ) VALUES (
                'helpdesk.ticket', %s, %s, 'comment', NULL,
                %s, %s, NOW(), NOW()
            )
            """
            
            # Format comment as HTML (Odoo format)
            html_comment = f'<div data-oe-version="1.2">{comment_text}</div>'
            
            cursor.execute(insert_comment_query, (ticket_id, html_comment, author_id, user_email))
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Comment added successfully to ticket {ticket_number} (ID: {ticket_id}) by {user_email} (partner_id: {author_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding comment to ticket {ticket_number}: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def get_recent_tickets_by_email(self, user_email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent tickets for a user by email
        
        Args:
            user_email: User email
            limit: Number of tickets to return
            
        Returns:
            List of recent tickets with basic info
        """
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT ht.id, ht.name, ht.number, 
                   CASE 
                       WHEN ht.stage_id = 1 THEN 'New'
                       WHEN ht.stage_id = 2 THEN 'In Progress'
                       WHEN ht.stage_id = 3 THEN 'Waiting'
                       WHEN ht.stage_id = 4 THEN 'Done'
                       WHEN ht.stage_id = 5 THEN 'Cancelled'
                       ELSE 'Unknown'
                   END as stage_name, 
                   ht.create_date
            FROM helpdesk_ticket ht
            WHERE ht.partner_email = %s OR ht.partner_email ILIKE %s
            ORDER BY ht.create_date DESC
            LIMIT %s
            """
            
            logger.info(f"Querying recent tickets for email: {user_email}")
            cursor.execute(query, (user_email, f"%{user_email}%", limit))
            rows = cursor.fetchall()
            logger.info(f"Query returned {len(rows)} rows")
            
            tickets = []
            for row in rows:
                ticket_info = {
                    'id': row[0],
                    'name': row[1],
                    'tracking_id': row[2],  # This is the number field
                    'stage_name': row[3] if row[3] else 'Unknown',
                    'create_date': row[4].strftime('%Y-%m-%d %H:%M') if row[4] else 'Unknown'
                }
                tickets.append(ticket_info)
            
            cursor.close()
            logger.info(f"Retrieved {len(tickets)} recent tickets for {user_email}")
            return tickets
            
        except Exception as e:
            logger.error(f"Error getting recent tickets for {user_email}: {e}")
            return []

    async def update_ticket_status(self, ticket_number: str, new_status: str) -> bool:
        """
        Update ticket status by ticket number
        
        Args:
            ticket_number: Ticket number (e.g., TH230925353)
            new_status: New status to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connection:
                logger.error("No database connection available")
                return False
            
            cursor = self.connection.cursor()
            
            # Map status names to stage_id using existing stage mapping
            stage_mapping = {
                1: "New",
                2: "In Progress", 
                3: "Waiting",
                4: "Done",
                5: "Cancelled"
            }
            
            # Reverse mapping: stage name -> stage_id
            reverse_mapping = {v.lower(): k for k, v in stage_mapping.items()}
            
            # Common status mappings
            status_mappings = {
                'resolved': 'done',
                'closed': 'done', 
                'completed': 'done',
                'finished': 'done',
                'solved': 'done',
                'new': 'new',
                'in progress': 'in progress',
                'waiting': 'waiting',
                'cancelled': 'cancelled'
            }
            
            # Get the normalized status
            normalized_status = status_mappings.get(new_status.lower(), new_status.lower())
            stage_id = reverse_mapping.get(normalized_status)
            
            if not stage_id:
                logger.error(f"Stage not found for status: {new_status} (normalized: {normalized_status})")
                cursor.close()
                return False
            
            # Update ticket status
            update_query = """
                UPDATE helpdesk_ticket 
                SET stage_id = %s
                WHERE number = %s OR name LIKE %s
            """
            
            cursor.execute(update_query, (stage_id, ticket_number, f'%{ticket_number}%'))
            rows_affected = cursor.rowcount
            
            if rows_affected > 0:
                self.connection.commit()
                logger.info(f"Successfully updated {rows_affected} ticket(s) with number {ticket_number} to status {new_status}")
                cursor.close()
                return True
            else:
                logger.warning(f"No tickets found with number {ticket_number}")
                cursor.close()
                return False
                
        except Exception as e:
            logger.error(f"Error updating ticket status for {ticket_number}: {e}")
            if self.connection:
                self.connection.rollback()
            return False

    def close(self) -> None:
        """Đóng kết nối database"""
        if self.connection:
            self.connection.close()
            logger.info("Đã đóng kết nối PostgreSQL")