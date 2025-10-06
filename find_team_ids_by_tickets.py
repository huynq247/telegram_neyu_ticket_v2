"""
Find Team IDs by Ticket Numbers
Tìm team_id của các teams dựa trên ticket numbers
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
load_dotenv()

from src.odoo.postgresql_connector import PostgreSQLConnector

def parse_odoo_url(odoo_url: str):
    """Parse ODOO_URL to extract host and port"""
    parsed = urlparse(odoo_url)
    host = parsed.hostname or parsed.netloc.split(':')[0]
    port = parsed.port or 15432
    return host, port

def find_team_ids():
    """Find team IDs for specific tickets"""
    print("=" * 70)
    print("🔍 FIND TEAM IDs BY TICKET NUMBERS")
    print("=" * 70)
    
    # Get configuration from .env
    odoo_url = os.getenv('ODOO_URL', '')
    odoo_db = os.getenv('ODOO_DB', '')
    odoo_username = os.getenv('ODOO_USERNAME', '')
    odoo_password = os.getenv('ODOO_PASSWORD', '')
    
    # Parse URL
    host, port = parse_odoo_url(odoo_url)
    
    print(f"\n🔗 Connecting to: {host}:{port}/{odoo_db}")
    
    # Connect to database
    try:
        connector = PostgreSQLConnector(
            host=host,
            port=port,
            database=odoo_db,
            username=odoo_username,
            password=odoo_password
        )
        
        print("✅ Connected successfully!\n")
        
        # Tickets to search for
        tickets_to_find = {
            'HT00011': 'Vietnam',
            'HT00012': 'Thailand',
            'HT00013': 'Malaysia',
            'HT00014': 'Indonesia',
            'HT00015': 'Philippines',
            'HT00016': 'India'
        }
        
        print("🔍 Searching for team IDs...\n")
        
        cursor = connector.connection.cursor()
        
        for ticket_number, country in tickets_to_find.items():
            try:
                # Search for ticket by name/number
                query = """
                    SELECT 
                        ht.id,
                        ht.name,
                        ht.team_id,
                        htt.name as team_name
                    FROM helpdesk_ticket ht
                    LEFT JOIN helpdesk_ticket_team htt ON ht.team_id = htt.id
                    WHERE ht.name LIKE %s
                    LIMIT 1;
                """
                
                cursor.execute(query, (f'%{ticket_number}%',))
                result = cursor.fetchone()
                
                if result:
                    ticket_id, ticket_name, team_id, team_name = result
                    print(f"✅ {country} ({ticket_number}):")
                    print(f"   Ticket ID: {ticket_id}")
                    print(f"   Ticket Name: {ticket_name}")
                    print(f"   Team ID: {team_id}")
                    print(f"   Team Name: {team_name}")
                    print()
                else:
                    print(f"❌ {country} ({ticket_number}): Không tìm thấy ticket")
                    print()
                    
            except Exception as e:
                print(f"❌ Error searching {ticket_number}: {e}")
                print()
        
        # Also show all teams in database
        print("\n" + "=" * 70)
        print("📊 ALL TEAMS IN DATABASE:")
        print("=" * 70)
        
        try:
            cursor.execute("""
                SELECT 
                    id,
                    name,
                    (SELECT COUNT(*) FROM helpdesk_ticket WHERE team_id = htt.id) as ticket_count
                FROM helpdesk_ticket_team htt
                ORDER BY id;
            """)
            
            teams = cursor.fetchall()
            
            if teams:
                print(f"\nFound {len(teams)} teams:\n")
                for team_id, team_name, ticket_count in teams:
                    print(f"   Team ID: {team_id:2d} | Name: {team_name:20s} | Tickets: {ticket_count}")
            else:
                print("\n⚠️  No teams found in database")
                
        except Exception as e:
            print(f"❌ Error listing teams: {e}")
        
        cursor.close()
        
        print("\n" + "=" * 70)
        print("✅ SCAN COMPLETED")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = find_team_ids()
    sys.exit(0 if success else 1)
