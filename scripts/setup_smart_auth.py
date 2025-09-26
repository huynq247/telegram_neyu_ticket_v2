#!/usr/bin/env python3
"""
Smart Auth Quick Setup
Thiết lập nhanh hệ thống smart authentication
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from src.telegram_bot.utils.smart_auth_utils import SmartAuthUtils
except ImportError:
    print("❌ Cannot import SmartAuthUtils. Make sure you're running from project root.")
    sys.exit(1)


def quick_setup():
    """Quick setup wizard for smart auth"""
    print("🚀 Smart Auth Quick Setup Wizard")
    print("=" * 50)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Ask for installation location
    auth_file_path = input("📄 Auth file path [user.auth.smart]: ").strip() or "user.auth.smart"
    
    # Check if file exists
    if os.path.exists(auth_file_path):
        print(f"⚠️  File {auth_file_path} already exists")
        action = input("Choose action - (o)verwrite, (b)ackup, (c)ancel [c]: ").lower().strip() or "c"
        
        if action == "c":
            print("❌ Setup cancelled")
            return False
        elif action == "b":
            backup_path = f"{auth_file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(auth_file_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
        elif action == "o":
            print("🗑️  Will overwrite existing file")
        else:
            print("❌ Invalid choice")
            return False
    
    print("\n🔧 Configuration Options:")
    print("1. 🏢 Production (Neyu company accounts)")
    print("2. 🔧 Development (Simple test accounts)")
    print("3. 🎯 Custom (Interactive setup)")
    
    config_type = input("Select configuration [1]: ").strip() or "1"
    
    try:
        if config_type == "1":
            success = create_production_config(auth_file_path)
        elif config_type == "2":
            success = create_development_config(auth_file_path)
        elif config_type == "3":
            success = create_custom_config(auth_file_path)
        else:
            print("❌ Invalid choice")
            return False
        
        if success:
            print(f"\n✅ Smart Auth setup completed!")
            print(f"📄 Auth file: {auth_file_path}")
            print("\n🚀 Next Steps:")
            print("1. Start your Telegram bot")
            print("2. Use /me command to test smart authentication")
            print("3. Check session management with enhanced features")
            
            # Show management commands
            print("\n🛠️  Management Commands:")
            print(f"python -m src.telegram_bot.utils.smart_auth_utils list-users {auth_file_path}")
            print(f"python -m src.telegram_bot.utils.smart_auth_utils add-user {auth_file_path}")
            print(f"python -m src.telegram_bot.utils.smart_auth_utils validate {auth_file_path}")
            
            return True
        else:
            print("❌ Setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False


def create_production_config(file_path: str) -> bool:
    """Create production configuration"""
    print("\n🏢 Creating production configuration...")
    
    config = {
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
                "last_used": None
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
                "last_used": None
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
                "last_used": None
            }
        },
        "metadata": {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "environment": "production",
            "description": "Production Smart Authentication Configuration",
            "security_level": "Tier 1 (Basic Protection)",
            "last_modified": datetime.now().isoformat()
        }
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Production config created with 3 users")
    return True


def create_development_config(file_path: str) -> bool:
    """Create development configuration"""
    print("\n🔧 Creating development configuration...")
    
    config = {
        "users": {
            "admin@dev.local": {
                "name": "Dev Admin",
                "password": SmartAuthUtils.encode_password("admin123"),
                "uid": "smart_dev_1",
                "partner_id": 1,
                "company_id": 1,
                "groups": ["Administration / Settings"],
                "is_helpdesk_manager": True,
                "is_helpdesk_user": True,
                "session_type": "admin_session",
                "created_at": datetime.now().isoformat(),
                "last_used": None
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
                "last_used": None
            }
        },
        "metadata": {
            "version": "1.0.0-dev",
            "created_at": datetime.now().isoformat(),
            "environment": "development",
            "description": "Development Smart Authentication Configuration",
            "security_level": "Development (Simple passwords)",
            "last_modified": datetime.now().isoformat()
        }
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Development config created")
    print("👥 Accounts: admin@dev.local/admin123, user@dev.local/user123")
    return True


def create_custom_config(file_path: str) -> bool:
    """Create custom configuration interactively"""
    print("\n🎯 Custom configuration setup...")
    
    config = {
        "users": {},
        "metadata": {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "environment": "custom",
            "description": "Custom Smart Authentication Configuration",
            "security_level": "Tier 1 (Basic Protection)",
            "last_modified": datetime.now().isoformat()
        }
    }
    
    print("👤 Add users (press Enter with empty email to finish):")
    user_count = 0
    
    while True:
        email = input(f"\nUser {user_count + 1} email: ").strip()
        if not email:
            break
        
        if not SmartAuthUtils.validate_email(email):
            print("❌ Invalid email format")
            continue
        
        name = input("Full name: ").strip()
        if not name:
            name = email.split('@')[0].title()
        
        password = input("Password [auto-generate]: ").strip()
        if not password:
            password = f"pass{user_count + 1:03d}"
        
        is_manager = input("Is manager? (y/n) [n]: ").lower().startswith('y')
        
        config["users"][email] = {
            "name": name,
            "password": SmartAuthUtils.encode_password(password),
            "uid": f"smart_custom_{user_count + 1}",
            "partner_id": user_count + 1,
            "company_id": 1,
            "groups": ["Help Desk Manager"] if is_manager else ["Help Desk User"],
            "is_helpdesk_manager": is_manager,
            "is_helpdesk_user": True,
            "session_type": "admin_session" if is_manager else "smart_auth",
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        user_count += 1
        print(f"✅ Added: {email} (password: {password})")
    
    if user_count == 0:
        print("❌ No users added")
        return False
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Custom config created with {user_count} users")
    return True


def check_system():
    """Check system requirements"""
    print("🔍 System Check")
    print("-" * 20)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if we can import required modules
    try:
        import json
        print("✅ JSON module: OK")
    except ImportError:
        print("❌ JSON module: FAILED")
        return False
    
    try:
        import base64
        print("✅ Base64 module: OK")
    except ImportError:
        print("❌ Base64 module: FAILED")
        return False
    
    # Check project structure
    expected_paths = [
        "src/telegram_bot/services",
        "src/telegram_bot/handlers",
        "src/telegram_bot/utils"
    ]
    
    for path in expected_paths:
        if os.path.exists(path):
            print(f"✅ {path}: OK")
        else:
            print(f"⚠️  {path}: Missing (may affect functionality)")
    
    print("✅ System check completed")
    return True


def main():
    """Main setup interface"""
    print("🚀 Smart Auth Quick Setup")
    print("=" * 50)
    
    # Check system first
    if not check_system():
        print("❌ System check failed")
        return
    
    print("\nOptions:")
    print("1. 🚀 Quick Setup (Recommended)")
    print("2. 📋 System Check Only")
    print("3. 🆘 Help")
    print("4. 🚪 Exit")
    
    try:
        choice = input("\nSelect option [1]: ").strip() or "1"
        
        if choice == "1":
            quick_setup()
        elif choice == "2":
            print("System check already completed above ✅")
        elif choice == "3":
            show_help()
        elif choice == "4":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled")


def show_help():
    """Show help information"""
    print("\n🆘 Smart Auth Help")
    print("=" * 30)
    print("This setup wizard creates a smart authentication file for the Telegram bot.")
    print("\n📝 What it does:")
    print("• Creates user credentials file (user.auth.smart)")
    print("• Sets up different user types and permissions")
    print("• Configures session timeout settings")
    print("• Enables file-based authentication")
    print("\n🔐 Security:")
    print("• Passwords are Base64 encoded (Tier 1 protection)")
    print("• File should have restricted permissions (chmod 600)")
    print("• Keep file secure and private")
    print("\n🛠️  After setup:")
    print("• Use /me command in Telegram to test")
    print("• Sessions timeout based on user type")
    print("• Activity tracking extends session automatically")


if __name__ == "__main__":
    main()