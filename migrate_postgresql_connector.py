#!/usr/bin/env python3
"""
Migration script to retire the old postgresql_connector.py and migrate to Clean Architecture.
This script helps transition from the monolithic 1105-line connector to the new structure.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.schema_service import DatabaseSchemaService
from src.infrastructure.adapters.legacy_data_adapter import LegacyDataAdapter
from src.infrastructure.repositories.legacy_ticket_repository import LegacyTicketRepository
from src.infrastructure.repositories.legacy_comment_repository import LegacyCommentRepository

logger = logging.getLogger(__name__)


class PostgreSQLConnectorMigrator:
    """Migrates from old postgresql_connector.py to new Clean Architecture"""
    
    def __init__(self, connection_string: str):
        """
        Initialize migrator
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.db_connection = DatabaseConnection()
        self.schema_service = None
        self.legacy_adapter = None
        self.ticket_repository = None
        self.comment_repository = None
    
    async def initialize(self) -> None:
        """Initialize all services"""
        try:
            # Parse connection string for connect method
            # Format: postgresql://user:pass@host:port/dbname
            import urllib.parse
            parsed = urllib.parse.urlparse(self.connection_string)
            
            await self.db_connection.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading /
                username=parsed.username,
                password=parsed.password
            )
            
            # Create services
            self.schema_service = DatabaseSchemaService(self.db_connection)
            self.legacy_adapter = LegacyDataAdapter(self.db_connection)
            
            # Create repositories
            self.ticket_repository = LegacyTicketRepository(
                self.db_connection, self.schema_service, self.legacy_adapter
            )
            self.comment_repository = LegacyCommentRepository(
                self.db_connection, self.schema_service, self.legacy_adapter
            )
            
            logger.info("Migration services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize migration services: {e}")
            raise
    
    async def analyze_legacy_structure(self) -> Dict[str, Any]:
        """
        Analyze the legacy database structure
        
        Returns:
            Analysis results
        """
        try:
            logger.info("🔍 Analyzing legacy database structure...")
            
            analysis = {
                'database_info': await self.schema_service.get_database_info(),
                'all_tables': await self.schema_service.get_all_tables(),
                'helpdesk_tables': await self.schema_service.find_helpdesk_tables(),
                'table_details': {}
            }
            
            # Analyze helpdesk tables in detail
            for table_name in analysis['helpdesk_tables']:
                table_info = await self.schema_service.describe_table(table_name)
                if table_info:
                    analysis['table_details'][table_name] = {
                        'columns': len(table_info.columns),
                        'row_count': table_info.row_count,
                        'sample_data': await self.schema_service.get_table_sample_data(table_name, 2)
                    }
            
            logger.info(f"✅ Analysis complete: {len(analysis['helpdesk_tables'])} helpdesk tables found")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing legacy structure: {e}")
            return {}
    
    async def test_legacy_data_access(self) -> Dict[str, Any]:
        """
        Test accessing legacy data through new repositories
        
        Returns:
            Test results
        """
        try:
            logger.info("🧪 Testing legacy data access...")
            
            results = {
                'tickets': {'status': 'failed', 'count': 0, 'samples': []},
                'comments': {'status': 'failed', 'count': 0, 'samples': []},
                'errors': []
            }
            
            # Test ticket migration
            try:
                migrated_tickets = await self.legacy_adapter.migrate_legacy_tickets(5)
                results['tickets'] = {
                    'status': 'success',
                    'count': len(migrated_tickets),
                    'samples': [
                        {
                            'number': t.number,
                            'title': t.title[:50] + '...' if len(t.title) > 50 else t.title,
                            'status': t.status.value,
                            'creator': t.creator_email
                        }
                        for t in migrated_tickets[:3]
                    ]
                }
                logger.info(f"✅ Successfully migrated {len(migrated_tickets)} tickets")
                
            except Exception as e:
                results['errors'].append(f"Ticket migration failed: {e}")
                logger.error(f"❌ Ticket migration failed: {e}")
            
            # Test comment migration for first ticket
            if results['tickets']['samples']:
                try:
                    first_ticket = results['tickets']['samples'][0]['number']
                    migrated_comments = await self.legacy_adapter.migrate_legacy_comments(first_ticket)
                    results['comments'] = {
                        'status': 'success',
                        'count': len(migrated_comments),
                        'samples': [
                            {
                                'ticket': c.ticket_number,
                                'author': c.author_email,
                                'content': c.content[:50] + '...' if len(c.content) > 50 else c.content,
                                'type': c.comment_type.value
                            }
                            for c in migrated_comments[:3]
                        ]
                    }
                    logger.info(f"✅ Successfully migrated {len(migrated_comments)} comments")
                    
                except Exception as e:
                    results['errors'].append(f"Comment migration failed: {e}")
                    logger.error(f"❌ Comment migration failed: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing legacy data access: {e}")
            return {'error': str(e)}
    
    async def create_new_tables_if_needed(self) -> Dict[str, bool]:
        """
        Create new clean architecture tables if they don't exist
        
        Returns:
            Creation results
        """
        try:
            logger.info("🏗️  Creating new Clean Architecture tables...")
            
            results = {
                'tickets_table': False,
                'comments_table': False
            }
            
            # Create tickets table
            results['tickets_table'] = await self.schema_service.create_tickets_table_if_not_exists()
            if results['tickets_table']:
                logger.info("✅ Tickets table created/verified")
            else:
                logger.error("❌ Failed to create tickets table")
            
            # Create comments table
            results['comments_table'] = await self.schema_service.create_comments_table_if_not_exists()
            if results['comments_table']:
                logger.info("✅ Comments table created/verified")
            else:
                logger.error("❌ Failed to create comments table")
            
            return results
            
        except Exception as e:
            logger.error(f"Error creating new tables: {e}")
            return {'error': str(e)}
    
    async def generate_migration_report(self) -> str:
        """
        Generate comprehensive migration report
        
        Returns:
            Migration report as string
        """
        try:
            report_lines = [
                "=" * 80,
                "🚀 POSTGRESQL_CONNECTOR.PY MIGRATION REPORT",
                "=" * 80,
                ""
            ]
            
            # Database analysis
            analysis = await self.analyze_legacy_structure()
            report_lines.extend([
                "📊 DATABASE ANALYSIS:",
                f"  • Database: {analysis.get('database_info', {}).get('database_name', 'Unknown')}",
                f"  • PostgreSQL Version: {analysis.get('database_info', {}).get('version', 'Unknown')[:50]}...",
                f"  • Total Tables: {analysis.get('database_info', {}).get('table_count', 0)}",
                f"  • Helpdesk Tables Found: {len(analysis.get('helpdesk_tables', []))}",
                ""
            ])
            
            # Table details
            if analysis.get('table_details'):
                report_lines.append("📋 HELPDESK TABLES DETAILS:")
                for table_name, details in analysis['table_details'].items():
                    report_lines.append(
                        f"  • {table_name}: {details['columns']} columns, {details['row_count']} rows"
                    )
                report_lines.append("")
            
            # Legacy data test
            test_results = await self.test_legacy_data_access()
            report_lines.extend([
                "🧪 LEGACY DATA ACCESS TEST:",
                f"  • Tickets Migration: {test_results.get('tickets', {}).get('status', 'unknown')} "
                f"({test_results.get('tickets', {}).get('count', 0)} records)",
                f"  • Comments Migration: {test_results.get('comments', {}).get('status', 'unknown')} "
                f"({test_results.get('comments', {}).get('count', 0)} records)",
                ""
            ])
            
            # Sample data
            if test_results.get('tickets', {}).get('samples'):
                report_lines.append("📝 SAMPLE MIGRATED TICKETS:")
                for ticket in test_results['tickets']['samples']:
                    report_lines.append(
                        f"  • {ticket['number']}: {ticket['title']} ({ticket['status']})"
                    )
                report_lines.append("")
            
            # New table creation
            table_results = await self.create_new_tables_if_needed()
            report_lines.extend([
                "🏗️  NEW TABLE CREATION:",
                f"  • Tickets Table: {'✅ Created/Verified' if table_results.get('tickets_table') else '❌ Failed'}",
                f"  • Comments Table: {'✅ Created/Verified' if table_results.get('comments_table') else '❌ Failed'}",
                ""
            ])
            
            # Migration recommendations
            report_lines.extend([
                "💡 MIGRATION RECOMMENDATIONS:",
                "",
                "1. IMMEDIATE ACTIONS:",
                "   • Replace postgresql_connector.py imports with new repositories",
                "   • Update dependency injection container",
                "   • Test new Clean Architecture components",
                "",
                "2. GRADUAL MIGRATION:",
                "   • Keep legacy tables for backward compatibility",
                "   • Use LegacyTicketRepository for seamless transition",
                "   • Gradually migrate data to new clean tables",
                "",
                "3. FINAL CLEANUP:",
                "   • Archive postgresql_connector.py",
                "   • Remove legacy table dependencies",
                "   • Update documentation",
                "",
                "4. NEW ARCHITECTURE BENEFITS:",
                "   • Single Responsibility Principle",
                "   • Better testability with dependency injection",
                "   • Cleaner separation of concerns",
                "   • Easier maintenance and debugging",
                ""
            ])
            
            # Errors if any
            if test_results.get('errors'):
                report_lines.extend([
                    "⚠️  ISSUES FOUND:",
                    ""
                ])
                for error in test_results['errors']:
                    report_lines.append(f"   • {error}")
                report_lines.append("")
            
            report_lines.extend([
                "=" * 80,
                "🎯 MIGRATION STATUS: " + (
                    "READY FOR TRANSITION" if not test_results.get('errors')
                    else "REQUIRES ATTENTION"
                ),
                "=" * 80
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating migration report: {e}")
            return f"Error generating report: {e}"
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.db_connection:
            await self.db_connection.disconnect()


async def main():
    """Main migration function"""
    print("🚀 PostgreSQL Connector Migration Tool")
    print("=" * 50)
    
    # Get connection string from environment or args
    connection_string = os.getenv('DATABASE_URL')
    if not connection_string:
        if len(sys.argv) > 1:
            connection_string = sys.argv[1]
        else:
            print("❌ Please provide DATABASE_URL environment variable or connection string as argument")
            print("Example: python migrate_postgresql_connector.py 'postgresql://user:pass@host:port/dbname'")
            return 1
    
    migrator = PostgreSQLConnectorMigrator(connection_string)
    
    try:
        # Initialize services
        await migrator.initialize()
        
        # Generate and display migration report
        report = await migrator.generate_migration_report()
        print(report)
        
        # Save report to file
        report_file = project_root / "MIGRATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📁 Full report saved to: {report_file}")
        
        return 0
        
    except Exception as e:
        print(f"💥 Migration failed: {e}")
        return 1
    
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run migration
    exit_code = asyncio.run(main())
    sys.exit(exit_code)