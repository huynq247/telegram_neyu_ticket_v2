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

# Query for the two tickets
query = """
    SELECT 
        id, 
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
    FROM helpdesk_ticket 
    WHERE name IN ('VN071025452', 'VN071025077')
    ORDER BY create_date DESC
"""

cur.execute(query)
rows = cur.fetchall()

print("\n" + "="*150)
print("TICKET DETAILS")
print("="*150)

for row in rows:
    print(f"\nTicket Name: {row[1]}")
    print(f"  ID: {row[0]}")
    print(f"  Partner ID: {row[2]}")
    print(f"  Partner Name: {row[3]}")
    print(f"  Partner Email: {row[4]}")
    print(f"  Description: {row[5][:100] if row[5] else 'None'}{'...' if row[5] and len(row[5]) > 100 else ''}")
    print(f"  Created: {row[6]}")
    print(f"  Modified: {row[7]}")
    print(f"  Assigned User ID: {row[8]}")
    print(f"  Stage ID: {row[9]}")
    print(f"  Created By User ID: {row[10]}")
    print(f"  Modified By User ID: {row[11]}")
    print("-"*150)

# Also get partner details
print("\n" + "="*150)
print("PARTNER DETAILS")
print("="*150)

for row in rows:
    if row[2]:  # if partner_id exists
        cur.execute("""
            SELECT id, name, email, phone, mobile, company_id, user_id
            FROM res_partner 
            WHERE id = %s
        """, (row[2],))
        partner = cur.fetchone()
        if partner:
            print(f"\nFor Ticket {row[1]}:")
            print(f"  Partner ID: {partner[0]}")
            print(f"  Partner Name: {partner[1]}")
            print(f"  Partner Email: {partner[2]}")
            print(f"  Partner Phone: {partner[3]}")
            print(f"  Partner Mobile: {partner[4]}")
            print(f"  Company ID: {partner[5]}")
            print(f"  User ID: {partner[6]}")
            print("-"*150)

# Get user details for created_by
print("\n" + "="*150)
print("CREATED BY USER DETAILS")
print("="*150)

for row in rows:
    if row[10]:  # if create_uid exists
        cur.execute("""
            SELECT id, login, partner_id
            FROM res_users 
            WHERE id = %s
        """, (row[10],))
        user = cur.fetchone()
        if user:
            print(f"\nFor Ticket {row[1]}:")
            print(f"  Created By User ID: {user[0]}")
            print(f"  Created By Login: {user[1]}")
            print(f"  Created By Partner ID: {user[2]}")
            
            # Get partner name for this user
            if user[2]:
                cur.execute("SELECT name FROM res_partner WHERE id = %s", (user[2],))
                partner_name = cur.fetchone()
                if partner_name:
                    print(f"  Created By Name: {partner_name[0]}")
            print("-"*150)

cur.close()
conn.close()

print("\n✅ Database scan completed!\n")
