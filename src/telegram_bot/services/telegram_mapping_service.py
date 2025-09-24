"""
Telegram User Mapping Service
Manages telegram_id <-> email mappings for smart auto-authentication
"""

import logging
import psycopg2
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import os
from ..utils.db_retry import db_retry
from ..utils.performance_monitor import monitor_db

logger = logging.getLogger(__name__)

class TelegramMappingService:
    """Service to manage telegram user mappings for auto-authentication"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Connect to PostgreSQL database - using Odoo database connection"""
        try:
            # Parse Odoo URL to get database connection details
            odoo_url = os.getenv('ODOO_URL', 'http://61.28.236.114:15432')
            
            # Extract host and port from ODOO_URL
            if '://' in odoo_url:
                url_parts = odoo_url.split('://', 1)[1]  # Remove protocol
                if ':' in url_parts:
                    host, port_str = url_parts.rsplit(':', 1)
                    port = int(port_str)
                else:
                    host = url_parts
                    port = 5432
            else:
                host = 'localhost'
                port = 5432
            
            database = os.getenv('ODOO_DB', 'service')
            username = os.getenv('ODOO_USERNAME', 'app_user') 
            password = os.getenv('ODOO_PASSWORD', 'S3cure!Pass')
            
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password
            )
            
            # Create table if not exists
            self._ensure_table_exists()
            logger.info("Connected to PostgreSQL for telegram mapping")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.connection = None
    
    def _ensure_table_exists(self):
        """Ensure telegram_user_mapping table exists"""
        try:
            cursor = self.connection.cursor()
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS telegram_user_mapping (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                email VARCHAR(255) NOT NULL,
                telegram_username VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
                is_active BOOLEAN DEFAULT TRUE
            );
            
            CREATE INDEX IF NOT EXISTS idx_telegram_mapping_telegram_id 
            ON telegram_user_mapping (telegram_id);
            
            CREATE INDEX IF NOT EXISTS idx_telegram_mapping_email 
            ON telegram_user_mapping (email);
            
            CREATE INDEX IF NOT EXISTS idx_telegram_mapping_expires_at 
            ON telegram_user_mapping (expires_at);
            """
            
            cursor.execute(create_table_sql)
            self.connection.commit()
            cursor.close()
            
            logger.info("Telegram mapping table created/verified successfully")
            
        except Exception as e:
            logger.error(f"Failed to create telegram mapping table: {e}")
            if self.connection:
                self.connection.rollback()
    
    @db_retry
    def save_mapping(self, telegram_id: int, email: str, telegram_username: Optional[str] = None) -> bool:
        """
        Save or update telegram_id -> email mapping
        
        Args:
            telegram_id: Telegram user ID
            email: User's email address
            telegram_username: Optional telegram username
            
        Returns:
            bool: True if successful
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Upsert: Insert or update if exists
            upsert_sql = """
            INSERT INTO telegram_user_mapping 
                (telegram_id, email, telegram_username, created_at, last_used, expires_at, is_active)
            VALUES 
                (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                 CURRENT_TIMESTAMP + INTERVAL '30 days', TRUE)
            ON CONFLICT (telegram_id) 
            DO UPDATE SET
                email = EXCLUDED.email,
                telegram_username = EXCLUDED.telegram_username,
                last_used = CURRENT_TIMESTAMP,
                expires_at = CURRENT_TIMESTAMP + INTERVAL '30 days',
                is_active = TRUE;
            """
            
            cursor.execute(upsert_sql, (telegram_id, email, telegram_username))
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Saved mapping: telegram_id={telegram_id} -> email={email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save mapping: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    @monitor_db
    @db_retry
    def get_email_for_telegram_id(self, telegram_id: int) -> Optional[str]:
        """
        Get email for telegram ID if mapping exists and not expired
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            str: Email if valid mapping exists, None otherwise
        """
        if not self.connection:
            logger.warning("No database connection available")
            return None
        
        try:
            cursor = self.connection.cursor()
            
            # Get active, non-expired mapping
            select_sql = """
            SELECT email, expires_at 
            FROM telegram_user_mapping 
            WHERE telegram_id = %s 
                AND is_active = TRUE 
                AND expires_at > CURRENT_TIMESTAMP;
            """
            
            cursor.execute(select_sql, (telegram_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                email, expires_at = result
                logger.info(f"Found valid mapping: telegram_id={telegram_id} -> email={email}, expires: {expires_at}")
                
                # Update last_used timestamp
                self._update_last_used(telegram_id)
                
                return email
            else:
                logger.debug(f"No valid mapping found for telegram_id={telegram_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get mapping: {e}")
            return None
    
    def _update_last_used(self, telegram_id: int):
        """Update last_used timestamp for a mapping"""
        try:
            cursor = self.connection.cursor()
            
            update_sql = """
            UPDATE telegram_user_mapping 
            SET last_used = CURRENT_TIMESTAMP 
            WHERE telegram_id = %s;
            """
            
            cursor.execute(update_sql, (telegram_id,))
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to update last_used: {e}")
    
    @db_retry
    def revoke_mapping(self, telegram_id: int) -> bool:
        """
        Revoke/deactivate mapping for telegram ID
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            bool: True if successful
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            update_sql = """
            UPDATE telegram_user_mapping 
            SET is_active = FALSE 
            WHERE telegram_id = %s;
            """
            
            cursor.execute(update_sql, (telegram_id,))
            affected_rows = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            if affected_rows > 0:
                logger.info(f"Revoked mapping for telegram_id={telegram_id}")
                return True
            else:
                logger.warning(f"No mapping found to revoke for telegram_id={telegram_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to revoke mapping: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    @db_retry
    def cleanup_expired_mappings(self) -> int:
        """
        Clean up expired mappings
        
        Returns:
            int: Number of mappings cleaned up
        """
        if not self.connection:
            logger.error("No database connection available")
            return 0
        
        try:
            cursor = self.connection.cursor()
            
            # Deactivate expired mappings
            cleanup_sql = """
            UPDATE telegram_user_mapping 
            SET is_active = FALSE 
            WHERE expires_at <= CURRENT_TIMESTAMP 
                AND is_active = TRUE;
            """
            
            cursor.execute(cleanup_sql)
            affected_rows = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            if affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} expired mappings")
            
            return affected_rows
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired mappings: {e}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    @db_retry
    def get_mapping_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed mapping information for telegram ID
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            dict: Mapping details or None
        """
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            
            select_sql = """
            SELECT telegram_id, email, telegram_username, created_at, 
                   last_used, expires_at, is_active
            FROM telegram_user_mapping 
            WHERE telegram_id = %s;
            """
            
            cursor.execute(select_sql, (telegram_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'telegram_id': result[0],
                    'email': result[1],
                    'telegram_username': result[2],
                    'created_at': result[3],
                    'last_used': result[4],
                    'expires_at': result[5],
                    'is_active': result[6],
                    'is_expired': result[5] <= datetime.now() if result[5] else True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get mapping info: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Closed telegram mapping database connection")