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

# Search for tickets with similar patterns
print("\n" + "="*150)
print("SEARCHING FOR TICKETS...")
print("="*150)

# Search by partial match
queries = [
    ("Exact match VN071025452", "SELECT name FROM helpdesk_ticket WHERE name = 'VN071025452'"),
    ("Exact match VN071025077", "SELECT name FROM helpdesk_ticket WHERE name = 'VN071025077'"),
    ("Pattern VN0710254%", "SELECT name FROM helpdesk_ticket WHERE name LIKE 'VN0710254%'"),
    ("Pattern VN0710250%", "SELECT name FROM helpdesk_ticket WHERE name LIKE 'VN0710250%'"),
    ("All tickets starting with VN07102", "SELECT name FROM helpdesk_ticket WHERE name LIKE 'VN07102%' ORDER BY create_date DESC LIMIT 20"),
    ("Recent tickets today", "SELECT name, partner_name, create_date FROM helpdesk_ticket WHERE DATE(create_date) = CURRENT_DATE ORDER BY create_date DESC LIMIT 10"),
]

for label, query in queries:
    print(f"\n{label}:")
    cur.execute(query)
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  {row}")
    else:
        print("  No results")

# Get latest tickets
print("\n" + "="*150)
print("LATEST 10 TICKETS IN DATABASE:")
print("="*150)

cur.execute("""
    SELECT 
        name, 
        partner_name, 
        partner_email,
        description,
        create_date,
        create_uid
    FROM helpdesk_ticket 
    ORDER BY create_date DESC 
    LIMIT 10
""")

rows = cur.fetchall()
for row in rows:
    print(f"\nTicket: {row[0]}")
    print(f"  Partner Name: {row[1]}")
    print(f"  Partner Email: {row[2]}")
    print(f"  Description: {row[3][:80] if row[3] else 'None'}{'...' if row[3] and len(row[3]) > 80 else ''}")
    print(f"  Created: {row[4]}")
    print(f"  Created By User ID: {row[5]}")
    
    # Get creator name
    if row[5]:
        cur.execute("""
            SELECT u.login, p.name 
            FROM res_users u
            LEFT JOIN res_partner p ON u.partner_id = p.id
            WHERE u.id = %s
        """, (row[5],))
        creator = cur.fetchone()
        if creator:
            print(f"  Created By: {creator[1]} ({creator[0]})")

cur.close()
conn.close()

print("\n✅ Search completed!\n")
