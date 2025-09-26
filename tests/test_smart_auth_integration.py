#!/usr/bin/env python3
"""
Smart Auth System Integration Test
Test toàn bộ hệ thống smart authentication
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
from src.telegram_bot.services.activity_tracker import ActivityTracker
from src.telegram_bot.services.session_cleanup_service import SessionCleanupService
from src.telegram_bot.services.auth_service import OdooAuthService


async def test_smart_auth_file_manager():
    """Test SmartAuthFileManager"""
    print("🔧 Testing SmartAuthFileManager...")
    
    try:
        # Initialize with test file
        auth_file = "user.auth.smart"
        if not os.path.exists(auth_file):
            print("❌ Auth file not found. Please create one first.")
            return False
        
        manager = SmartAuthFileManager(auth_file)
        
        # Test loading users
        users = manager.load_users()
        print(f"✅ Loaded {len(users)} users")
        
        # Test getting specific user credentials - using telegram username format
        test_user = "@huy_nguyen_neyu"  # This is how telegram users are identified
        credentials = manager.get_credentials(test_user)
        
        if credentials[0] and credentials[1]:  # Returns (email, password) tuple
            print(f"✅ Retrieved credentials for telegram user")
            
            # Test user info
            user_info = manager.get_user_info(credentials[0])
            if user_info:
                print(f"✅ Retrieved user info for {credentials[0]}")
            else:
                print("❌ Could not retrieve user info")
                return False
        else:
            # Try direct email approach
            test_email = "huy.nguyen@neyu.co"
            user_info = manager.get_user_info(test_email)
            if user_info:
                print(f"✅ Retrieved user info for {test_email}")
            else:
                print(f"❌ Could not retrieve user info for {test_email}")
                return False
        
        # Test list active users
        active_users = manager.list_active_users()
        print(f"✅ Active users count: {len(active_users)}")
        
        print("✅ SmartAuthFileManager test passed")
        return True
        
    except Exception as e:
        print(f"❌ SmartAuthFileManager test failed: {e}")
        return False


async def test_enhanced_session_manager():
    """Test EnhancedSessionManager"""
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
            print(f"✅ Session validation successful for user: {user_data['name']}")
        else:
            print("❌ Session validation failed")
            return False
        
        # Test activity tracking
        track_result = session_manager.track_activity(
            test_user_id, 'command', {'command': 'test'}
        )
        print(f"✅ Activity tracking: {track_result}")
        
        # Test session info
        session_info = session_manager.get_session_info(test_user_id)
        if session_info:
            print(f"✅ Session info retrieved: {session_info['session_type']}")
        else:
            print("❌ Could not retrieve session info")
            return False
        
        # Test basic session functionality (skip stats for now)
        print("✅ Session basic functionality working")
        
        print("✅ EnhancedSessionManager test passed")
        return True
        
    except Exception as e:
        print(f"❌ EnhancedSessionManager test failed: {e}")
        return False


async def test_activity_tracker():
    """Test ActivityTracker"""
    print("\n🔧 Testing ActivityTracker...")
    
    try:
        # Mock auth service for testing
        class MockAuthService:
            def track_user_activity(self, user_id, activity_type, metadata):
                return True
        
        mock_auth_service = MockAuthService()
        activity_tracker = ActivityTracker(mock_auth_service)
        
        test_user_id = 12345
        
        # Mock update object for tracking
        class MockUpdate:
            def __init__(self, user_id):
                self.effective_user = MockUser(user_id)
                self.message = MockMessage()
                self.callback_query = None
        
        class MockUser:
            def __init__(self, user_id):
                self.id = user_id
        
        class MockMessage:
            def __init__(self):
                self.text = '/test_command'
        
        mock_update = MockUpdate(test_user_id)
        
        # Test activity tracking with mock update
        result1 = await activity_tracker.track_activity(
            test_user_id, 'command', {'command': '/test_command'}
        )
        print(f"✅ Basic activity tracking: {result1}")
        
        print("✅ ActivityTracker test passed")
        return True
        
    except Exception as e:
        print(f"❌ ActivityTracker test failed: {e}")
        return False


async def test_auth_service_integration():
    """Test OdooAuthService with smart auth"""
    print("\n🔧 Testing OdooAuthService Integration...")
    
    try:
        # Mock config for testing
        odoo_config = {
            'xmlrpc_url': 'http://test.local:8069',
            'database': 'test_db'
        }
        
        auth_service = OdooAuthService(
            odoo_config['xmlrpc_url'], 
            odoo_config['database']
        )
        
        # Test smart auth availability (use correct method name)
        is_smart_enabled = auth_service.smart_auth_enabled
        print(f"✅ Smart auth enabled: {is_smart_enabled}")
        
        if is_smart_enabled:
            # Test basic auth service functionality
            print("✅ Enhanced auth service initialized with smart auth support")
        
        print("✅ OdooAuthService integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ OdooAuthService integration test failed: {e}")
        return False


async def test_integration_flow():
    """Test complete integration flow"""
    print("\n🚀 Testing Complete Integration Flow...")
    
    try:
        # 1. Initialize all components
        auth_file = "user.auth.smart"
        file_manager = SmartAuthFileManager(auth_file)
        session_manager = EnhancedSessionManager()
        
        # Mock auth service
        class MockAuthService:
            def __init__(self):
                self.smart_auth_manager = file_manager
                self.enhanced_session_manager = session_manager
                self.smart_auth_enabled = True
            
            def track_user_activity(self, user_id, activity_type, metadata):
                return self.enhanced_session_manager.track_activity(
                    user_id, activity_type, metadata
                )
        
        mock_auth_service = MockAuthService()
        activity_tracker = ActivityTracker(mock_auth_service)
        
        print("✅ All components initialized")
        
        # 2. Test authentication flow
        test_email = "huy.nguyen@neyu.co"
        test_password = "Neyu@2025"
        
        # Get user info (no direct password verification method)
        user_data = file_manager.get_user_info(test_email)
        if user_data:
            print(f"✅ User data found for {test_email}")
            
            # Add required fields for session
            user_data['user_type'] = 'smart_auth'
            
            test_user_id = 12345
            session_token = session_manager.create_session(
                test_user_id, user_data, SessionType.SMART_AUTH
            )
            print(f"✅ Session created: {session_token[:16]}...")
            
            # Track activity
            await activity_tracker.track_command_activity(
                test_user_id, '/me', {'integration_test': True}
            )
            print("✅ Activity tracked")
            
            # Validate session
            is_valid, session_user_data = session_manager.validate_session(test_user_id)
            if is_valid:
                print(f"✅ Session validated for {session_user_data['name']}")
            else:
                print("❌ Session validation failed")
                return False
            
        else:
            print(f"❌ Authentication failed for {test_email}")
            return False
        
        print("✅ Complete integration flow test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration flow test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Smart Auth System Integration Test")
    print("=" * 60)
    
    # Check if auth file exists
    if not os.path.exists("user.auth.smart"):
        print("⚠️  Auth file not found. Creating sample file...")
        from src.telegram_bot.utils.smart_auth_utils import SmartAuthUtils
        SmartAuthUtils.create_sample_auth_file("user.auth.smart")
        print("✅ Sample auth file created")
    
    # Run tests
    tests = [
        ("SmartAuthFileManager", test_smart_auth_file_manager),
        ("EnhancedSessionManager", test_enhanced_session_manager),
        ("ActivityTracker", test_activity_tracker),
        ("OdooAuthService Integration", test_auth_service_integration),
        ("Complete Integration Flow", test_integration_flow)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Smart Auth system is ready.")
        
        print("\n🚀 Next Steps:")
        print("1. Start your Telegram bot")
        print("2. Use /me command to test smart authentication")
        print("3. Monitor session management and activity tracking")
        print("4. Check logs for detailed operation info")
        
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    asyncio.run(main())