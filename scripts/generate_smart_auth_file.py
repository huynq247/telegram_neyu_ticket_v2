#!/usr/bin/env python3
"""
Sample Smart Auth File Generator
Tạo file user.auth.smart mẫu cho hệ thống smart authentication
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project path to sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.telegram_bot.utils.smart_auth_utils import SmartAuthUtils


def generate_production_sample():
    """Generate production-ready sample file"""
    file_path = "user.auth.smart"
    
    print("🚀 Smart Auth Sample Generator")
    print("=" * 40)
    
    # Check if file exists
    if os.path.exists(file_path):
        overwrite = input(f"File {file_path} exists. Overwrite? (y/n): ").lower().startswith('y')
        if not overwrite:
            print("❌ Generation cancelled")
            return False
    
    try:
        # Create comprehensive sample data
        sample_data = {
            "users": {
                "huy.nguyen@neyu.co": {
                    "name": "Huy Nguyen",
                    "password": SmartAuthUtils.encode_password("Neyu@2025"),
                    "uid": "smart_1001",
                    "partner_id": 1,
                    "company_id": 1,
                    "groups": ["IT Services", "Help Desk Manager", "Administration / Settings"],
                    "is_helpdesk_manager": True,
                    "is_helpdesk_user": True,
                    "session_type": "admin_session",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Admin user with full access"
                },
                "huy.nguyen@ultrafresh.asia": {
                    "name": "Huy Nguyen (Ultrafresh)",
                    "password": SmartAuthUtils.encode_password("Neyu@2025"),
                    "uid": "smart_1002",
                    "partner_id": 3,
                    "company_id": 1,
                    "groups": ["IT Services", "Help Desk Manager"],
                    "is_helpdesk_manager": True,
                    "is_helpdesk_user": True,
                    "session_type": "admin_session",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Cross-domain admin access"
                },
                "eric.tra@neyu.co": {
                    "name": "Eric Tra",
                    "password": SmartAuthUtils.encode_password("Neyu@2025"),
                    "uid": "smart_1003",
                    "partner_id": 2,
                    "company_id": 1,
                    "groups": ["Help Desk User"],
                    "is_helpdesk_manager": False,
                    "is_helpdesk_user": True,
                    "session_type": "smart_auth",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Regular helpdesk user"
                },
                "support@neyu.co": {
                    "name": "Support Team",
                    "password": SmartAuthUtils.encode_password("Support@2025"),
                    "uid": "smart_1004", 
                    "partner_id": 4,
                    "company_id": 1,
                    "groups": ["Help Desk User", "Support Team"],
                    "is_helpdesk_manager": False,
                    "is_helpdesk_user": True,
                    "session_type": "smart_auth",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Shared support account"
                },
                "test@example.com": {
                    "name": "Test User",
                    "password": SmartAuthUtils.encode_password("test123"),
                    "uid": "smart_1005",
                    "partner_id": 5,
                    "company_id": 1,
                    "groups": ["Portal User"],
                    "is_helpdesk_manager": False,
                    "is_helpdesk_user": False,
                    "session_type": "manual_login",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Testing account with limited access"
                }
            },
            "metadata": {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "created_by": "Smart Auth Sample Generator",
                "description": "Smart Authentication Configuration File for Telegram Bot",
                "security_level": "Tier 1 (Basic Protection)",
                "encoding": "Base64",
                "last_modified": datetime.now().isoformat(),
                "total_users": 5,
                "session_types": {
                    "admin_session": "8 hours inactivity timeout",
                    "smart_auth": "24 hours inactivity timeout", 
                    "manual_login": "48 hours inactivity timeout"
                },
                "features": [
                    "File-based authentication",
                    "Inactivity-based session timeout", 
                    "Activity tracking",
                    "Session warnings",
                    "Multiple session types"
                ],
                "security_notes": [
                    "Passwords are Base64 encoded (Tier 1 security)",
                    "For production, consider stronger encryption",
                    "Keep this file secure and private",
                    "Regular password rotation recommended"
                ]
            }
        }
        
        # Save file with nice formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sample auth file created: {file_path}")
        print(f"📊 Users created: {len(sample_data['users'])}")
        print("\n👥 User Accounts:")
        print("-" * 50)
        
        for email, user in sample_data["users"].items():
            decoded_password = SmartAuthUtils.decode_password(user["password"])
            print(f"📧 {email}")
            print(f"   👤 Name: {user['name']}")
            print(f"   🔑 Password: {decoded_password}")
            print(f"   🏷️  Session Type: {user['session_type']}")
            print(f"   ⚡ Manager: {'Yes' if user['is_helpdesk_manager'] else 'No'}")
            print(f"   💬 {user.get('notes', 'No notes')}")
            print()
        
        print("🔧 Next Steps:")
        print("1. Move this file to your project root directory")
        print("2. Secure file permissions (chmod 600)")
        print("3. Test authentication with /me command")
        print("4. Consider changing default passwords")
        print("\n🛠️  Management Commands:")
        print("python smart_auth_utils.py list-users          # List all users")
        print("python smart_auth_utils.py add-user            # Add new user")
        print("python smart_auth_utils.py change-password     # Change password")
        print("python smart_auth_utils.py validate            # Validate file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating sample file: {e}")
        return False


def generate_development_sample():
    """Generate development/testing sample file"""
    file_path = "user.auth.smart.dev"
    
    print("🔧 Development Sample Generator")
    print("=" * 40)
    
    try:
        dev_data = {
            "users": {
                "admin@dev.local": {
                    "name": "Dev Admin",
                    "password": SmartAuthUtils.encode_password("admin123"),
                    "uid": "smart_dev_1",
                    "partner_id": 1,
                    "company_id": 1,
                    "groups": ["Administration / Settings", "Help Desk Manager"],
                    "is_helpdesk_manager": True,
                    "is_helpdesk_user": True,
                    "session_type": "admin_session",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Development admin account"
                },
                "user@dev.local": {
                    "name": "Dev User",
                    "password": SmartAuthUtils.encode_password("user123"),
                    "uid": "smart_dev_2",
                    "partner_id": 2,
                    "company_id": 1,
                    "groups": ["Help Desk User"],
                    "is_helpdesk_manager": False,
                    "is_helpdesk_user": True,
                    "session_type": "smart_auth",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Development user account"
                },
                "test@dev.local": {
                    "name": "Test User",
                    "password": SmartAuthUtils.encode_password("test123"),
                    "uid": "smart_dev_3",
                    "partner_id": 3,
                    "company_id": 1,
                    "groups": ["Portal User"],
                    "is_helpdesk_manager": False,
                    "is_helpdesk_user": False,
                    "session_type": "manual_login",
                    "created_at": datetime.now().isoformat(),
                    "last_used": None,
                    "notes": "Testing account"
                }
            },
            "metadata": {
                "version": "1.0.0-dev",
                "created_at": datetime.now().isoformat(),
                "environment": "development",
                "description": "Development Smart Auth Configuration",
                "security_level": "Development (Simple passwords)",
                "last_modified": datetime.now().isoformat()
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(dev_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Development auth file created: {file_path}")
        print("\n👥 Development Accounts:")
        
        for email, user in dev_data["users"].items():
            decoded_password = SmartAuthUtils.decode_password(user["password"])
            print(f"  • {email} / {decoded_password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating development file: {e}")
        return False


def main():
    """Main generator interface"""
    print("🚀 Smart Auth File Generator")
    print("=" * 50)
    print("1. Production Sample (user.auth.smart)")
    print("2. Development Sample (user.auth.smart.dev)")
    print("3. Both files")
    print("4. Exit")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            generate_production_sample()
        elif choice == "2":
            generate_development_sample()
        elif choice == "3":
            print("Generating both files...\n")
            generate_production_sample()
            print("\n" + "="*50 + "\n")
            generate_development_sample()
        elif choice == "4":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Generation cancelled")


if __name__ == "__main__":
    main()