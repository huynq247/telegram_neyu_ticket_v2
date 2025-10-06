"""
Check which tables are being used in the system
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.odoo.postgresql_connector import PostgreSQLConnector

def parse_odoo_url(odoo_url: str):
    parsed = urlparse(odoo_url)
    host = parsed.hostname or parsed.netloc.split(':')[0]
    port = parsed.port or 15432
    return host, port

def check_tables():
    print("=" * 70)
    print("🔍 CHECKING TABLES IN DATABASE")
    print("=" * 70)
    
    odoo_url = os.getenv('ODOO_URL', '')
    odoo_db = os.getenv('ODOO_DB', '')
    odoo_username = os.getenv('ODOO_USERNAME', '')
    odoo_password = os.getenv('ODOO_PASSWORD', '')
    
    host, port = parse_odoo_url(odoo_url)
    
    print(f"\n🔗 Connecting to: {host}:{port}/{odoo_db}")
    
    try:
        connector = PostgreSQLConnector(
            host=host,
            port=port,
            database=odoo_db,
            username=odoo_username,
            password=odoo_password
        )
        
        print("✅ Connected successfully!\n")
        
        cursor = connector.connection.cursor()
        
        # Check if project_task exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'project_task'
            );
        """)
        project_task_exists = cursor.fetchone()[0]
        
        # Check if helpdesk_ticket exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'helpdesk_ticket'
            );
        """)
        helpdesk_ticket_exists = cursor.fetchone()[0]
        
        print("📊 TABLE STATUS:")
        print(f"   project_task: {'✅ EXISTS' if project_task_exists else '❌ NOT FOUND'}")
        print(f"   helpdesk_ticket: {'✅ EXISTS' if helpdesk_ticket_exists else '❌ NOT FOUND'}")
        
        # Count records in each
        if project_task_exists:
            cursor.execute("SELECT COUNT(*) FROM project_task;")
            count = cursor.fetchone()[0]
            print(f"\n   project_task records: {count}")
        
        if helpdesk_ticket_exists:
            cursor.execute("SELECT COUNT(*) FROM helpdesk_ticket;")
            count = cursor.fetchone()[0]
            print(f"   helpdesk_ticket records: {count}")
        
        # Check columns in project_task if exists
        if project_task_exists:
            print("\n📋 COLUMNS IN project_task:")
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'project_task'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            has_x_tracking_id = False
            for col_name, col_type in columns[:20]:  # Show first 20
                if col_name == 'x_tracking_id':
                    has_x_tracking_id = True
                    print(f"   ✅ {col_name}: {col_type}")
                else:
                    print(f"      {col_name}: {col_type}")
            
            if not has_x_tracking_id:
                print(f"\n   ❌ x_tracking_id NOT FOUND in project_task!")
        
        cursor.close()
        
        print("\n" + "=" * 70)
        print("✅ CHECK COMPLETED")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_tables()
    sys.exit(0 if success else 1)
