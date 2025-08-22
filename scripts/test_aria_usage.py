#!/usr/bin/env python3
"""
Test Runner for ARIA Snapshot Usage
===================================

This script provides an easy way to run different types of tests
for the ARIA snapshot functionality.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def main():
    """Main test runner function"""
    print("ARIA Snapshot Usage Test Runner")
    print("==============================")
    
    # Check if we're in the right directory
    if not os.path.exists("examples/aria_snapshot_usage.py"):
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected to find: examples/aria_snapshot_usage.py")
        return 1
    
    # Test categories to run
    test_options = {
        "1": ("Unit Tests Only", [
            "python", "-m", "pytest", 
            "tests/unit/test_aria_snapshot_usage.py", 
            "-v", "--tb=short"
        ]),
        "2": ("Integration Tests Only", [
            "python", "-m", "pytest", 
            "tests/integration/test_aria_snapshot_integration.py", 
            "-v", "--tb=short", "-m", "not slow"
        ]),
        "3": ("All Tests (excluding slow)", [
            "python", "-m", "pytest", 
            "tests/unit/test_aria_snapshot_usage.py",
            "tests/integration/test_aria_snapshot_integration.py",
            "-v", "--tb=short", "-m", "not slow"
        ]),
        "4": ("All Tests (including slow)", [
            "python", "-m", "pytest", 
            "tests/unit/test_aria_snapshot_usage.py",
            "tests/integration/test_aria_snapshot_integration.py",
            "-v", "--tb=short"
        ]),
        "5": ("Smoke Test (basic functionality)", [
            "python", "-m", "pytest", 
            "tests/unit/test_aria_snapshot_usage.py::TestARIASnapshotExamples::test_setup_and_cleanup",
            "-v"
        ]),
        "6": ("Run with Coverage", [
            "python", "-m", "pytest", 
            "tests/unit/test_aria_snapshot_usage.py",
            "tests/integration/test_aria_snapshot_integration.py",
            "--cov=examples", "--cov-report=html", "--cov-report=term-missing",
            "-m", "not slow"
        ])
    }
    
    print("\nAvailable test options:")
    for key, (description, _) in test_options.items():
        print(f"  {key}: {description}")
    
    print("\nAdditional options:")
    print("  7: Check test dependencies")
    print("  8: Run example manually (demo)")
    print("  0: Exit")
    
    while True:
        choice = input("\nEnter your choice (0-8): ").strip()
        
        if choice == "0":
            print("Exiting...")
            break
        elif choice == "7":
            check_dependencies()
        elif choice == "8":
            run_manual_demo()
        elif choice in test_options:
            description, cmd = test_options[choice]
            success = run_command(cmd, description)
            if not success:
                print("\n⚠️  Some tests failed. Check the output above for details.")
        else:
            print("❌ Invalid choice. Please enter a number between 0-8.")
    
    return 0


def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n" + "="*60)
    print("Checking Test Dependencies")
    print("="*60)
    
    required_packages = [
        "pytest",
        "playwright",
    ]
    
    optional_packages = [
        "pytest-cov",
        "pytest-timeout",
        "pytest-mock"
    ]
    
    print("\nRequired packages:")
    all_required_available = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (REQUIRED)")
            all_required_available = False
    
    print("\nOptional packages:")
    for package in optional_packages:
        try:
            if package == "pytest-cov":
                __import__("pytest_cov")
            elif package == "pytest-timeout":
                __import__("pytest_timeout")
            elif package == "pytest-mock":
                __import__("pytest_mock")
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ⚠️  {package} (optional)")
    
    if not all_required_available:
        print("\n❌ Some required packages are missing.")
        print("Install them with: pip install pytest playwright")
        print("Then run: playwright install")
    else:
        print("\n✅ All required dependencies are available!")
    
    # Check Playwright browsers
    print("\nChecking Playwright browsers...")
    try:
        result = subprocess.run(
            ["python", "-m", "playwright", "install", "--dry-run"], 
            capture_output=True, text=True, timeout=10
        )
        if "chromium" in result.stdout.lower():
            print("  ✅ Playwright browsers check completed")
        else:
            print("  ⚠️  Playwright browsers may need installation")
            print("     Run: playwright install")
    except Exception as e:
        print(f"  ⚠️  Could not check Playwright browsers: {e}")


def run_manual_demo():
    """Run the ARIA snapshot usage example manually"""
    print("\n" + "="*60)
    print("Running Manual Demo")
    print("="*60)
    
    print("\n⚠️  This will open a browser window and run the demo.")
    print("Make sure you have Playwright installed and browsers set up.")
    
    choice = input("Continue? (y/N): ").strip().lower()
    if choice != 'y':
        print("Demo cancelled.")
        return
    
    try:
        # Import and run the demo
        sys.path.append(str(Path(__file__).parent / "examples"))
        from aria_snapshot_usage import demo_usage
        
        print("\nStarting demo...")
        demo_usage()
        print("\n✅ Demo completed successfully!")
        
    except ImportError as e:
        print(f"❌ Could not import demo: {e}")
        print("Make sure the examples/aria_snapshot_usage.py file exists.")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)