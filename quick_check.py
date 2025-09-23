#!/usr/bin/env python3
"""
Quick test script to verify project setup and run basic checks.
This helps identify issues before running the full test suite.
"""
import sys
import os
import importlib
from pathlib import Path

def colored_print(message, color="green"):
    """Print colored output"""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m"
    }
    
    color_code = colors.get(color, colors["reset"])
    reset_code = colors["reset"]
    print(f"{color_code}{message}{reset_code}")

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        colored_print(f"✅ {description}: {filepath}", "green")
        return True
    else:
        colored_print(f"❌ {description} NOT FOUND: {filepath}", "red")
        return False

def check_import(module_name, description):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        colored_print(f"✅ {description}: {module_name}", "green")
        return True
    except ImportError as e:
        colored_print(f"❌ {description} FAILED: {module_name} ({e})", "red")
        return False

def check_directory_structure():
    """Check project directory structure"""
    colored_print("\n🏗️  CHECKING PROJECT STRUCTURE", "blue")
    
    directories = [
        ("src/domain/entities", "Domain entities directory"),
        ("src/domain/repositories", "Domain repositories directory"),
        ("src/application/use_cases", "Application use cases directory"),
        ("src/application/dto", "Application DTOs directory"),
        ("src/infrastructure/repositories", "Infrastructure repositories directory"),
        ("src/infrastructure/database", "Infrastructure database directory"),
        ("src/presentation/handlers", "Presentation handlers directory"),
        ("src/presentation/formatters", "Presentation formatters directory"),
        ("tests/unit/domain", "Unit tests domain directory"),
        ("tests/unit/application", "Unit tests application directory"),
        ("tests/integration/infrastructure", "Integration tests directory")
    ]
    
    passed = 0
    for dir_path, description in directories:
        if Path(dir_path).exists():
            colored_print(f"✅ {description}: {dir_path}", "green")
            passed += 1
        else:
            colored_print(f"❌ {description} NOT FOUND: {dir_path}", "red")
    
    return passed, len(directories)

def check_key_files():
    """Check existence of key project files"""
    colored_print("\n📁 CHECKING KEY FILES", "blue")
    
    files = [
        ("src/app.py", "Main application entry point"),
        ("src/container.py", "Dependency injection container"),
        ("src/config/container_config.py", "Container configuration"),
        ("requirements.txt", "Main dependencies"),
        ("requirements-test.txt", "Test dependencies"),
        ("pytest.ini", "Pytest configuration"),
        ("run_tests.py", "Test runner script"),
        ("tests/conftest.py", "Test fixtures"),
        ("TEST_CHECKLIST.md", "Test checklist"),
        (".env.example", "Environment variables example")
    ]
    
    passed = 0
    for filepath, description in files:
        if check_file_exists(filepath, description):
            passed += 1
    
    return passed, len(files)

def check_dependencies():
    """Check if key dependencies can be imported"""
    colored_print("\n📦 CHECKING DEPENDENCIES", "blue")
    
    # Main dependencies
    main_deps = [
        ("telegram", "python-telegram-bot"),
        ("asyncpg", "AsyncPG PostgreSQL driver"),
        ("pydantic", "Pydantic data validation"),
        ("dotenv", "python-dotenv")
    ]
    
    # Test dependencies
    test_deps = [
        ("pytest", "Pytest testing framework"),
        ("pytest_asyncio", "Pytest async support"),
        ("unittest.mock", "Mock testing utilities")
    ]
    
    colored_print("Main Dependencies:", "yellow")
    main_passed = 0
    for module, description in main_deps:
        if check_import(module, description):
            main_passed += 1
    
    colored_print("\nTest Dependencies:", "yellow")
    test_passed = 0
    for module, description in test_deps:
        if check_import(module, description):
            test_passed += 1
    
    return main_passed, len(main_deps), test_passed, len(test_deps)

def check_project_imports():
    """Check if project modules can be imported"""
    colored_print("\n🐍 CHECKING PROJECT IMPORTS", "blue")
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    modules = [
        ("src.domain.entities.comment", "Comment entity"),
        ("src.domain.entities.ticket", "Ticket entity"),
        ("src.domain.entities.user", "User entity"),
        ("src.application.use_cases.view_comments", "ViewComments use case"),
        ("src.application.use_cases.add_comment", "AddComment use case"),
        ("src.application.dto", "Application DTOs"),
        ("src.infrastructure.repositories.postgresql_comment_repository", "PostgreSQL Comment Repository"),
        ("src.presentation.handlers.comment_handler", "Comment Handler"),
        ("src.container", "DI Container"),
    ]
    
    passed = 0
    for module, description in modules:
        if check_import(module, description):
            passed += 1
    
    return passed, len(modules)

def test_basic_functionality():
    """Test basic functionality of key components"""
    colored_print("\n⚡ TESTING BASIC FUNCTIONALITY", "blue")
    
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Test Comment entity creation
        from src.domain.entities.comment import Comment, CommentType
        comment = Comment(
            ticket_number="TKT-001",
            content="Test comment",
            author_email="test@example.com"
        )
        colored_print("✅ Comment entity creation works", "green")
        
        # Test Comment validation
        assert comment.content == "Test comment"
        assert comment.comment_type == CommentType.PUBLIC
        colored_print("✅ Comment entity validation works", "green")
        
        # Test DTOs
        from src.application.dto import ViewCommentsRequest
        request = ViewCommentsRequest(
            ticket_number="TKT-001",
            user_email="test@example.com"
        )
        colored_print("✅ DTO creation works", "green")
        
        return 3, 3
        
    except Exception as e:
        colored_print(f"❌ Basic functionality test failed: {e}", "red")
        return 0, 3

def main():
    """Main check function"""
    colored_print("🚀 TELEGRAM BOT PROJECT QUICK CHECK", "blue")
    colored_print("=" * 50, "blue")
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    total_passed = 0
    total_checks = 0
    
    # Check directory structure
    passed, total = check_directory_structure()
    total_passed += passed
    total_checks += total
    
    # Check key files
    passed, total = check_key_files()
    total_passed += passed
    total_checks += total
    
    # Check dependencies
    main_passed, main_total, test_passed, test_total = check_dependencies()
    total_passed += main_passed + test_passed
    total_checks += main_total + test_total
    
    # Check project imports
    passed, total = check_project_imports()
    total_passed += passed
    total_checks += total
    
    # Test basic functionality
    passed, total = test_basic_functionality()
    total_passed += passed
    total_checks += total
    
    # Summary
    colored_print("\n" + "=" * 50, "blue")
    colored_print("📊 SUMMARY", "blue")
    colored_print(f"Total checks: {total_checks}", "yellow")
    colored_print(f"Passed: {total_passed}", "green")
    colored_print(f"Failed: {total_checks - total_passed}", "red")
    
    percentage = (total_passed / total_checks) * 100 if total_checks > 0 else 0
    colored_print(f"Success rate: {percentage:.1f}%", "yellow")
    
    if percentage >= 80:
        colored_print("\n🎉 PROJECT SETUP LOOKS GOOD!", "green")
        colored_print("You can proceed with running tests:", "green")
        colored_print("  python run_tests.py unit", "yellow")
        colored_print("  python run_tests.py all", "yellow")
    elif percentage >= 50:
        colored_print("\n⚠️  PROJECT SETUP NEEDS ATTENTION", "yellow")
        colored_print("Some issues found. Check the checklist: TEST_CHECKLIST.md", "yellow")
    else:
        colored_print("\n💥 PROJECT SETUP HAS MAJOR ISSUES", "red")
        colored_print("Please follow the checklist: TEST_CHECKLIST.md", "red")
    
    colored_print("\nNext steps:", "blue")
    colored_print("1. Fix any issues shown above", "yellow")
    colored_print("2. Install missing dependencies: pip install -r requirements.txt", "yellow")
    colored_print("3. Install test dependencies: pip install -r requirements-test.txt", "yellow")
    colored_print("4. Run the full test suite: python run_tests.py all", "yellow")
    
    return 0 if percentage >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())