#!/usr/bin/env python3
"""
Smart Authentication Utilities
Công cụ hỗ trợ cho hệ thống smart authentication
"""
import base64
import json
import os
import hashlib
from typing import Dict, Any, Optional
import getpass
from datetime import datetime

class SmartAuthUtils:
    """Utilities for smart authentication management"""
    
    @staticmethod
    def encode_password(password: str) -> str:
        """
        Encode password using base64 (Tier 1 security)
        
        Args:
            password: Plain text password
            
        Returns:
            encoded_password: Base64 encoded password
        """
        return base64.b64encode(password.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def decode_password(encoded_password: str) -> str:
        """
        Decode base64 encoded password
        
        Args:
            encoded_password: Base64 encoded password
            
        Returns:
            password: Plain text password
        """
        return base64.b64decode(encoded_password.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def generate_uid(email: str) -> str:
        """
        Generate consistent UID from email
        
        Args:
            email: User email
            
        Returns:
            uid: Generated user ID
        """
        return f"smart_{hash(email) % 10000}"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation
        
        Args:
            email: Email to validate
            
        Returns:
            valid: True if email format is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def create_sample_auth_file(file_path: str = "user.auth.smart") -> bool:
        """
        Create sample user.auth.smart file with example data
        
        Args:
            file_path: Path to auth file
            
        Returns:
            success: True if file created successfully
        """
        try:
            sample_data = {
                "users": {
                    "huy.nguyen@neyu.co": {
                        "name": "Huy Nguyen",
                        "password": SmartAuthUtils.encode_password("Neyu@2025"),
                        "uid": "smart_1001",
                        "partner_id": 1,
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
                        "uid": "smart_1002",
                        "partner_id": 2,
                        "company_id": 1,
                        "groups": ["Help Desk User"],
                        "is_helpdesk_manager": False,
                        "is_helpdesk_user": True,
                        "session_type": "smart_auth",
                        "created_at": datetime.now().isoformat(),
                        "last_used": None
                    },
                    "demo@example.com": {
                        "name": "Demo User",
                        "password": SmartAuthUtils.encode_password("demo123"),
                        "uid": "smart_1003",
                        "partner_id": 3,
                        "company_id": 1,
                        "groups": ["Portal User"],
                        "is_helpdesk_manager": False,
                        "is_helpdesk_user": False,
                        "session_type": "manual_login",
                        "created_at": datetime.now().isoformat(),
                        "last_used": None
                    }
                },
                "metadata": {
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "description": "Smart Authentication Configuration File",
                    "security_level": "Tier 1 (Basic Protection)",
                    "last_modified": datetime.now().isoformat()
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Sample auth file created: {file_path}")
            print("\n📋 Sample users:")
            for email, user in sample_data["users"].items():
                decoded_password = SmartAuthUtils.decode_password(user["password"])
                print(f"  • {email} (password: {decoded_password})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating sample file: {e}")
            return False
    
    @staticmethod
    def add_user_interactive(file_path: str = "user.auth.smart") -> bool:
        """
        Interactive user addition to auth file
        
        Args:
            file_path: Path to auth file
            
        Returns:
            success: True if user added successfully
        """
        try:
            print("🔧 Smart Auth - Add New User")
            print("=" * 40)
            
            # Get user input
            email = input("Email: ").strip()
            if not SmartAuthUtils.validate_email(email):
                print("❌ Invalid email format")
                return False
            
            name = input("Full Name: ").strip()
            if not name:
                print("❌ Name is required")
                return False
            
            password = getpass.getpass("Password: ").strip()
            if not password:
                print("❌ Password is required")
                return False
            
            # Optional fields
            is_manager = input("Is Helpdesk Manager? (y/n): ").lower().startswith('y')
            is_user = input("Is Helpdesk User? (y/n): ").lower().startswith('y')
            
            session_type = "admin_session" if is_manager else ("smart_auth" if is_user else "manual_login")
            
            # Load existing file or create new
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "users": {},
                    "metadata": {
                        "version": "1.0.0",
                        "created_at": datetime.now().isoformat(),
                        "description": "Smart Authentication Configuration File",
                        "security_level": "Tier 1 (Basic Protection)"
                    }
                }
            
            # Check if user exists
            if email in data["users"]:
                overwrite = input(f"User {email} exists. Overwrite? (y/n): ").lower().startswith('y')
                if not overwrite:
                    print("❌ User addition cancelled")
                    return False
            
            # Add user
            data["users"][email] = {
                "name": name,
                "password": SmartAuthUtils.encode_password(password),
                "uid": SmartAuthUtils.generate_uid(email),
                "partner_id": len(data["users"]) + 1,
                "company_id": 1,
                "groups": ["Help Desk Manager", "Help Desk User"] if is_manager else (["Help Desk User"] if is_user else ["Portal User"]),
                "is_helpdesk_manager": is_manager,
                "is_helpdesk_user": is_user,
                "session_type": session_type,
                "created_at": datetime.now().isoformat(),
                "last_used": None
            }
            
            # Update metadata
            data["metadata"]["last_modified"] = datetime.now().isoformat()
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ User added successfully: {email}")
            print(f"📄 Auth file updated: {file_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
    
    @staticmethod
    def list_users(file_path: str = "user.auth.smart") -> bool:
        """
        List all users in auth file
        
        Args:
            file_path: Path to auth file
            
        Returns:
            success: True if listing successful
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ Auth file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📋 Smart Auth Users ({file_path})")
            print("=" * 60)
            
            if not data.get("users"):
                print("No users found")
                return True
            
            for i, (email, user) in enumerate(data["users"].items(), 1):
                print(f"{i}. {user['name']} <{email}>")
                print(f"   UID: {user['uid']}")
                print(f"   Groups: {', '.join(user['groups'])}")
                print(f"   Manager: {'Yes' if user['is_helpdesk_manager'] else 'No'}")
                print(f"   Session Type: {user['session_type']}")
                print(f"   Created: {user['created_at']}")
                print(f"   Last Used: {user['last_used'] or 'Never'}")
                print()
            
            # Show metadata
            if "metadata" in data:
                print("📊 File Metadata:")
                print(f"   Version: {data['metadata'].get('version', 'Unknown')}")
                print(f"   Security Level: {data['metadata'].get('security_level', 'Unknown')}")
                print(f"   Last Modified: {data['metadata'].get('last_modified', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
            return False
    
    @staticmethod
    def change_password(file_path: str = "user.auth.smart") -> bool:
        """
        Change user password in auth file
        
        Args:
            file_path: Path to auth file
            
        Returns:
            success: True if password changed successfully
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ Auth file not found: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data.get("users"):
                print("❌ No users found in auth file")
                return False
            
            print("🔧 Smart Auth - Change Password")
            print("=" * 40)
            
            # List users
            emails = list(data["users"].keys())
            for i, email in enumerate(emails, 1):
                print(f"{i}. {data['users'][email]['name']} <{email}>")
            
            # Get user selection
            try:
                choice = int(input("\nSelect user (number): ")) - 1
                if choice < 0 or choice >= len(emails):
                    print("❌ Invalid selection")
                    return False
                
                selected_email = emails[choice]
            except ValueError:
                print("❌ Invalid input")
                return False
            
            # Get new password
            new_password = getpass.getpass("New Password: ").strip()
            if not new_password:
                print("❌ Password cannot be empty")
                return False
            
            confirm_password = getpass.getpass("Confirm Password: ").strip()
            if new_password != confirm_password:
                print("❌ Passwords do not match")
                return False
            
            # Update password
            data["users"][selected_email]["password"] = SmartAuthUtils.encode_password(new_password)
            data["metadata"]["last_modified"] = datetime.now().isoformat()
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Password changed for: {selected_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error changing password: {e}")
            return False
    
    @staticmethod
    def validate_auth_file(file_path: str = "user.auth.smart") -> bool:
        """
        Validate auth file structure and data
        
        Args:
            file_path: Path to auth file
            
        Returns:
            valid: True if file is valid
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ Auth file not found: {file_path}")
                return False
            
            print(f"🔍 Validating auth file: {file_path}")
            print("=" * 50)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            errors = []
            warnings = []
            
            # Check structure
            if "users" not in data:
                errors.append("Missing 'users' section")
            
            if "metadata" not in data:
                warnings.append("Missing 'metadata' section")
            
            # Validate users
            if "users" in data:
                for email, user in data["users"].items():
                    # Check email format
                    if not SmartAuthUtils.validate_email(email):
                        errors.append(f"Invalid email format: {email}")
                    
                    # Check required fields
                    required_fields = ["name", "password", "uid"]
                    for field in required_fields:
                        if field not in user:
                            errors.append(f"Missing field '{field}' for user: {email}")
                    
                    # Check password encoding
                    if "password" in user:
                        try:
                            SmartAuthUtils.decode_password(user["password"])
                        except Exception:
                            errors.append(f"Invalid password encoding for user: {email}")
                    
                    # Check boolean fields
                    bool_fields = ["is_helpdesk_manager", "is_helpdesk_user"]
                    for field in bool_fields:
                        if field in user and not isinstance(user[field], bool):
                            warnings.append(f"Field '{field}' should be boolean for user: {email}")
            
            # Report results
            if errors:
                print("❌ Validation Errors:")
                for error in errors:
                    print(f"   • {error}")
            
            if warnings:
                print("⚠️  Validation Warnings:")
                for warning in warnings:
                    print(f"   • {warning}")
            
            if not errors and not warnings:
                print("✅ Auth file is valid")
                user_count = len(data.get("users", {}))
                print(f"📊 Total users: {user_count}")
                return True
            elif not errors:
                print("✅ Auth file is valid (with warnings)")
                return True
            else:
                print("❌ Auth file has errors")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False


def main():
    """Main CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 Smart Auth Utilities")
        print("=" * 30)
        print("Usage: python smart_auth_utils.py <command> [options]")
        print("\nCommands:")
        print("  create-sample [file]    - Create sample auth file")
        print("  add-user [file]         - Add user interactively")
        print("  list-users [file]       - List all users")
        print("  change-password [file]  - Change user password")
        print("  validate [file]         - Validate auth file")
        print("  encode <password>       - Encode password")
        print("  decode <encoded>        - Decode password")
        print("\nDefault file: user.auth.smart")
        return
    
    command = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else "user.auth.smart"
    
    if command == "create-sample":
        SmartAuthUtils.create_sample_auth_file(file_path)
    elif command == "add-user":
        SmartAuthUtils.add_user_interactive(file_path)
    elif command == "list-users":
        SmartAuthUtils.list_users(file_path)
    elif command == "change-password":
        SmartAuthUtils.change_password(file_path)
    elif command == "validate":
        SmartAuthUtils.validate_auth_file(file_path)
    elif command == "encode":
        if len(sys.argv) < 3:
            print("❌ Password required")
            return
        password = sys.argv[2]
        encoded = SmartAuthUtils.encode_password(password)
        print(f"Encoded: {encoded}")
    elif command == "decode":
        if len(sys.argv) < 3:
            print("❌ Encoded password required")
            return
        encoded = sys.argv[2]
        try:
            decoded = SmartAuthUtils.decode_password(encoded)
            print(f"Decoded: {decoded}")
        except Exception as e:
            print(f"❌ Decoding error: {e}")
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()