#!/usr/bin/env python3
"""
Test runner script for the Telegram support bot.
Provides convenient commands for running different types of tests.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the result"""
    print(f"\n🔄 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(result.stdout)
    else:
        print(f"❌ {description} failed")
        if result.stderr.strip():
            print("Error output:")
            print(result.stderr)
        if result.stdout.strip():
            print("Standard output:")
            print(result.stdout)
        return False
    
    return True


def run_unit_tests():
    """Run unit tests only"""
    cmd = ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
    return run_command(cmd, "Running unit tests")


def run_integration_tests():
    """Run integration tests only"""
    cmd = ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
    return run_command(cmd, "Running integration tests")


def run_all_tests():
    """Run all tests with coverage"""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=term-missing"]
    return run_command(cmd, "Running all tests with coverage")


def run_tests_with_html_report():
    """Run tests and generate HTML coverage report"""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html:htmlcov", "--cov-report=term"]
    return run_command(cmd, "Running tests with HTML coverage report")


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    cmd = ["python", "-m", "pytest", test_path, "-v", "--tb=short"]
    return run_command(cmd, f"Running specific test: {test_path}")


def run_fast_tests():
    """Run only fast tests (exclude slow marker)"""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "-m", "not slow", "--tb=short"]
    return run_command(cmd, "Running fast tests only")


def install_test_dependencies():
    """Install test dependencies"""
    cmd = ["pip", "install", "-r", "requirements-test.txt"]
    return run_command(cmd, "Installing test dependencies")


def check_test_environment():
    """Check if test environment is properly set up"""
    print("🔍 Checking test environment...")
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} is available")
    except ImportError:
        print("❌ pytest is not installed")
        return False
    
    # Check if test directories exist
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ tests directory not found")
        return False
    
    unit_dir = test_dir / "unit"
    integration_dir = test_dir / "integration"
    
    if unit_dir.exists():
        print(f"✅ Unit tests directory found ({len(list(unit_dir.rglob('test_*.py')))} test files)")
    else:
        print("⚠️  Unit tests directory not found")
    
    if integration_dir.exists():
        print(f"✅ Integration tests directory found ({len(list(integration_dir.rglob('test_*.py')))} test files)")
    else:
        print("⚠️  Integration tests directory not found")
    
    return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Test runner for Telegram support bot")
    parser.add_argument("command", nargs="?", default="all", 
                       choices=["unit", "integration", "all", "html", "fast", "install", "check"],
                       help="Test command to run")
    parser.add_argument("--test", "-t", help="Run specific test file or function")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    if project_root != Path.cwd():
        print(f"📁 Changing to project directory: {project_root}")
        import os
        os.chdir(project_root)
    
    success = True
    
    if args.command == "check":
        success = check_test_environment()
    elif args.command == "install":
        success = install_test_dependencies()
    elif args.test:
        success = run_specific_test(args.test)
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "all":
        success = run_all_tests()
    elif args.command == "html":
        success = run_tests_with_html_report()
        if success:
            print("\n📊 HTML coverage report generated in 'htmlcov' directory")
            print("Open 'htmlcov/index.html' in your browser to view the report")
    elif args.command == "fast":
        success = run_fast_tests()
    
    if success:
        print("\n🎉 Test execution completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()