"""
Check project_task table schema
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

def check_schema():
    odoo_url = os.getenv('ODOO_URL', '')
    odoo_db = os.getenv('ODOO_DB', '')
    odoo_username = os.getenv('ODOO_USERNAME', '')
    odoo_password = os.getenv('ODOO_PASSWORD', '')
    
    host, port = parse_odoo_url(odoo_url)
    
    connector = PostgreSQLConnector(
        host=host,
        port=port,
        database=odoo_db,
        username=odoo_username,
        password=odoo_password
    )
    
    cursor = connector.connection.cursor()
    
    # Check if project_task table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'project_task'
        );
    """)
    exists = cursor.fetchone()[0]
    print(f"project_task table exists: {exists}")
    
    if exists:
        # Get columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'project_task'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"\nColumns in project_task ({len(columns)}):")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
    
    cursor.close()

if __name__ == "__main__":
    check_schema()
