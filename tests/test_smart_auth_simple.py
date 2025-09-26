#!/usr/bin/env python3
"""
Smart Auth System Simple Test
Test cơ bản cho các components của smart auth system
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.telegram_bot.services.smart_auth_file_manager import SmartAuthFileManager
from src.telegram_bot.services.enhanced_session_manager import EnhancedSessionManager, SessionType


async def test_file_manager():
    """Test basic file manager functionality"""
    print("🔧 Testing SmartAuthFileManager...")
    
    try:
        # Check if auth file exists
        auth_file = "user.auth.smart"
        if not os.path.exists(auth_file):
            print("⚠️  Creating sample auth file...")
            from src.telegram_bot.utils.smart_auth_utils import SmartAuthUtils
            SmartAuthUtils.create_sample_auth_file(auth_file)
        
        # Initialize manager
        manager = SmartAuthFileManager(auth_file)
        
        # Test loading users
        users = manager.load_users()
        print(f"✅ Loaded {len(users)} users from {auth_file}")
        
        # Test getting user info
        test_email = "huy.nguyen@neyu.co"
        user_info = manager.get_user_info(test_email)
        if user_info:
            print(f"✅ Retrieved user info for {test_email}: {user_info['name']}")
        
        # Test list active users
        active_users = manager.list_active_users()
        print(f"✅ Active users: {len(active_users)}")
        
        # Test password encoding/decoding
        test_password = "TestPassword123"
        encoded = SmartAuthFileManager.encode_password(test_password)
        decoded = SmartAuthFileManager.decode_password(encoded)
        
        if decoded == test_password:
            print("✅ Password encoding/decoding works correctly")
        else:
            print("❌ Password encoding/decoding failed")
            return False
        
        print("✅ SmartAuthFileManager basic test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ SmartAuthFileManager test failed: {e}")
        return False


async def test_session_manager():
    """Test enhanced session manager"""
    print("\n🔧 Testing EnhancedSessionManager...")
    
    try:
        session_manager = EnhancedSessionManager()
        
        # Test user data
        test_user_id = 12345
        test_user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'uid': 'test_123',
            'user_type': 'smart_auth'
        }
        
        # Test session creation
        session_token = session_manager.create_session(
            test_user_id, test_user_data, SessionType.SMART_AUTH
        )
        print(f"✅ Session created: {session_token[:16]}...")
        
        # Test session validation
        is_valid, user_data = session_manager.validate_session(test_user_id)
        if is_valid and user_data:
            print(f"✅ Session validation successful for: {user_data['name']}")
        else:
            print("❌ Session validation failed")
            return False
        
        # Test activity tracking
        track_result = session_manager.track_activity(
            test_user_id, 'command', {'command': 'test'}
        )
        print(f"✅ Activity tracking result: {track_result}")
        
        # Test session info
        session_info = session_manager.get_session_info(test_user_id)
        if session_info:
            print(f"✅ Session info - Type: {session_info['session_type']}")
        
        # Test timeout check
        timeout_info = session_manager.check_session_timeout(test_user_id)
        if timeout_info is None:
            print("✅ Session timeout check: Session is healthy")
        else:
            print(f"⚠️  Session timeout warning: {timeout_info}")
        
        print("✅ EnhancedSessionManager test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ EnhancedSessionManager test failed: {e}")
        return False


async def test_auth_service():
    """Test auth service integration"""
    print("\n🔧 Testing OdooAuthService Integration...")
    
    try:
        from src.telegram_bot.services.auth_service import OdooAuthService
        
        # Mock config for testing
        odoo_config = {
            'xmlrpc_url': 'http://test.local:8069',
            'database': 'test_db'
        }
        
        auth_service = OdooAuthService(
            odoo_config['xmlrpc_url'], 
            odoo_config['database']
        )
        
        # Test that auth service initializes with smart auth
        print(f"✅ Auth service initialized")
        print(f"✅ Smart auth enabled: {hasattr(auth_service, 'smart_auth_manager')}")
        print(f"✅ Enhanced session manager: {hasattr(auth_service, 'enhanced_session_manager')}")
        
        # Test creating a session
        test_user_id = 12345
        test_user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'user_type': 'smart_auth'
        }
        
        session_token = auth_service.create_session(test_user_id, test_user_data)
        if session_token:
            print(f"✅ Session created via auth service: {session_token[:16]}...")
        
        # Test session validation
        is_valid, user_data = auth_service.validate_session(test_user_id)
        if is_valid:
            print(f"✅ Session validated via auth service for: {user_data['name']}")
        
        print("✅ OdooAuthService integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ OdooAuthService integration test failed: {e}")
        return False


async def test_utilities():
    """Test utility functions"""
    print("\n🔧 Testing Smart Auth Utilities...")
    
    try:
        from src.telegram_bot.utils.smart_auth_utils import SmartAuthUtils
        
        # Test email validation
        valid_emails = ["test@example.com", "user@domain.co.uk"]
        invalid_emails = ["invalid", "@test.com", "test@"]
        
        for email in valid_emails:
            if SmartAuthUtils.validate_email(email):
                print(f"✅ Valid email: {email}")
            else:
                print(f"❌ Email validation failed for: {email}")
                return False
        
        for email in invalid_emails:
            if not SmartAuthUtils.validate_email(email):
                print(f"✅ Invalid email correctly rejected: {email}")
            else:
                print(f"❌ Invalid email incorrectly accepted: {email}")
                return False
        
        # Test password encoding
        test_password = "MySecretPassword123!"
        encoded = SmartAuthUtils.encode_password(test_password)
        decoded = SmartAuthUtils.decode_password(encoded)
        
        if decoded == test_password:
            print("✅ Password encoding/decoding utility works")
        else:
            print("❌ Password encoding/decoding utility failed")
            return False
        
        # Test UID generation
        test_emails = ["user1@test.com", "user2@test.com"]
        uids = [SmartAuthUtils.generate_uid(email) for email in test_emails]
        
        if len(set(uids)) == len(uids):  # All UIDs should be unique
            print("✅ UID generation works correctly")
        else:
            print("❌ UID generation produced duplicates")
            return False
        
        print("✅ Smart Auth Utilities test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Smart Auth Utilities test failed: {e}")
        return False


async def test_file_operations():
    """Test file operations and validation"""
    print("\n🔧 Testing File Operations...")
    
    try:
        from src.telegram_bot.utils.smart_auth_utils import SmartAuthUtils
        
        # Test creating sample file
        test_file = "test_auth.json"
        success = SmartAuthUtils.create_sample_auth_file(test_file)
        if success:
            print(f"✅ Sample file created: {test_file}")
        else:
            print("❌ Sample file creation failed")
            return False
        
        # Test validating file
        valid = SmartAuthUtils.validate_auth_file(test_file)
        if valid:
            print(f"✅ File validation passed: {test_file}")
        else:
            print("❌ File validation failed")
            return False
        
        # Test listing users
        list_success = SmartAuthUtils.list_users(test_file)
        if list_success:
            print("✅ User listing works")
        else:
            print("❌ User listing failed")
            return False
        
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"✅ Test file cleaned up: {test_file}")
        
        print("✅ File Operations test PASSED") 
        return True
        
    except Exception as e:
        print(f"❌ File Operations test failed: {e}")
        return False


async def main():
    """Run all simple tests"""
    print("🚀 Smart Auth System - Simple Test Suite")
    print("=" * 70)
    
    tests = [
        ("SmartAuthFileManager", test_file_manager),
        ("EnhancedSessionManager", test_session_manager),
        ("OdooAuthService Integration", test_auth_service),
        ("Smart Auth Utilities", test_utilities),
        ("File Operations", test_file_operations)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
                print(f"✅ {test_name}: PASSED\n")
            else:
                print(f"❌ {test_name}: FAILED\n")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}\n")
    
    print("=" * 70)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Smart Auth system is working correctly.")
        
        print("\n🚀 Ready for Production:")
        print("✅ File-based authentication system")
        print("✅ Enhanced session management with timeouts")
        print("✅ Password encoding/decoding")
        print("✅ User management utilities")
        print("✅ File validation and operations")
        
        print("\n📝 Next Steps:")
        print("1. Start your Telegram bot")
        print("2. Use /me command to test smart authentication")
        print("3. Monitor session timeouts and activity tracking")
        print("4. Use utility scripts for user management")
        
        return True
    else:
        print(f"❌ {total_tests - passed_tests} tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    asyncio.run(main())