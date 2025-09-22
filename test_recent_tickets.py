#!/usr/bin/env python3
"""
Test script for recent tickets functionality
"""
import sys
import os
sys.path.append('.')

from config.settings import Settings
from src.odoo.postgresql_connector import PostgreSQLConnector

def test_recent_tickets():
    try:
        # Get database config
        settings = Settings()
        
        # Parse host and port from odoo_url
        odoo_url = settings.odoo_url
        if "://" in odoo_url:
            odoo_url = odoo_url.split("://")[1]
        if ":" in odoo_url:
            host, port = odoo_url.split(":")
        else:
            host = odoo_url
            port = "5432"
        
        # Create connector
        connector = PostgreSQLConnector(
            host=host,
            port=int(port),
            database=settings.odoo_db,
            username=settings.odoo_username,
            password=settings.odoo_password
        )
        
        cursor = connector.connection.cursor()
        
        # Check total tickets
        cursor.execute('SELECT COUNT(*) FROM helpdesk_ticket')
        total = cursor.fetchone()[0]
        print(f'Total tickets in database: {total}')
        
        # Check tickets with partner_email
        cursor.execute('SELECT COUNT(*) FROM helpdesk_ticket WHERE partner_email IS NOT NULL')
        with_email = cursor.fetchone()[0]
        print(f'Tickets with partner_email: {with_email}')
        
        # Check available tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%helpdesk%'")
        tables = cursor.fetchall()
        print(f'Available helpdesk tables: {[row[0] for row in tables]}')
        
        # Check stage field in helpdesk_ticket
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'helpdesk_ticket' AND column_name LIKE '%stage%'")
        stage_columns = cursor.fetchall()
        print(f'Stage-related columns in helpdesk_ticket: {[row[0] for row in stage_columns]}')
        
        # Show some sample data without stage join
        cursor.execute('''
            SELECT ht.number, ht.partner_email, ht.create_date
            FROM helpdesk_ticket ht
            WHERE ht.partner_email IS NOT NULL
            ORDER BY ht.create_date DESC
            LIMIT 5
        ''')
        samples = cursor.fetchall()
        print(f'\nSample tickets:')
        for row in samples:
            print(f'  {row[0]} | {row[1]} | {row[2]}')
        
        # Test the actual method with different emails
        test_emails = ["huy.nguyen@neyu.co", "huy.nguyen@kiwi-eco.com", "huy.nguyen@ultrafresh.asia"]
        
        for test_email in test_emails:
            print(f'\nTesting get_recent_tickets_by_email with: {test_email}')
            recent = connector.get_recent_tickets_by_email(test_email, 5)
            print(f'Result: {len(recent)} tickets')
            for ticket in recent:
                print(f'  - {ticket["tracking_id"]} | {ticket["stage_name"]} | {ticket["create_date"]}')
        
        cursor.close()
        connector.close()
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recent_tickets()