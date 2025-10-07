import psycopg2
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host='206.189.94.245',
    port=15432,
    dbname='odoo18_helpdesk',
    user='app_user',
    password='Vn9!qT2#Lx8pZk5$'
)

cur = conn.cursor()

ticket_numbers = ['VN071025452', 'VN071025077']

print("\n" + "="*150)
print("SEARCHING TICKETS BY NUMBER FIELD")
print("="*150)

# Search in all destination tables
tables = [
    'helpdesk_ticket',
    'helpdesk_ticket_thailand',
    'helpdesk_ticket_india',
    'helpdesk_ticket_singapore',
    'helpdesk_ticket_philippines',
    'helpdesk_ticket_malaysia',
    'helpdesk_ticket_indonesia'
]

for ticket_num in ticket_numbers:
    print(f"\n{'='*150}")
    print(f"🔍 Searching for Ticket Number: {ticket_num}")
    print('='*150)
    found = False
    
    for table in tables:
        try:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            
            if not cur.fetchone()[0]:
                continue
                
            # Search for ticket
            query = f"""
                SELECT 
                    id,
                    number,
                    name,
                    partner_id,
                    partner_name,
                    partner_email,
                    description,
                    create_date,
                    write_date,
                    user_id,
                    stage_id,
                    create_uid,
                    write_uid
                FROM {table}
                WHERE number = %s
            """
            
            cur.execute(query, (ticket_num,))
            row = cur.fetchone()
            
            if row:
                found = True
                print(f"\n✅ Found in table: {table}")
                print(f"  Ticket ID: {row[0]}")
                print(f"  Number: {row[1]}")
                print(f"  Name: {row[2]}")
                print(f"  Partner ID: {row[3]}")
                print(f"  Partner Name: {row[4]}")
                print(f"  Partner Email: {row[5]}")
                print(f"  Description: {row[6][:100] if row[6] else 'None'}{'...' if row[6] and len(row[6]) > 100 else ''}")
                print(f"  Created: {row[7]}")
                print(f"  Modified: {row[8]}")
                print(f"  Assigned User ID: {row[9]}")
                print(f"  Stage ID: {row[10]}")
                print(f"  Created By User ID: {row[11]}")
                print(f"  Modified By User ID: {row[12]}")
                
                # Get partner details
                if row[3]:
                    cur.execute("""
                        SELECT id, name, email, phone, mobile
                        FROM res_partner 
                        WHERE id = %s
                    """, (row[3],))
                    partner = cur.fetchone()
                    if partner:
                        print(f"\n  📋 Partner Details:")
                        print(f"     Partner ID: {partner[0]}")
                        print(f"     Name: {partner[1]}")
                        print(f"     Email: {partner[2]}")
                        print(f"     Phone: {partner[3]}")
                        print(f"     Mobile: {partner[4]}")
                
                # Get creator details
                if row[11]:
                    cur.execute("""
                        SELECT u.id, u.login, p.name
                        FROM res_users u
                        LEFT JOIN res_partner p ON u.partner_id = p.id
                        WHERE u.id = %s
                    """, (row[11],))
                    creator = cur.fetchone()
                    if creator:
                        print(f"\n  👤 Created By:")
                        print(f"     User ID: {creator[0]}")
                        print(f"     Login: {creator[1]}")
                        print(f"     Name: {creator[2]}")
                
                break  # Found in this table, no need to check others
                
        except Exception as e:
            print(f"  ⚠️ Error checking {table}: {e}")
    
    if not found:
        print(f"\n❌ Ticket {ticket_num} not found in any table")

cur.close()
conn.close()

print("\n" + "="*150)
print("✅ Search completed!")
print("="*150 + "\n")
