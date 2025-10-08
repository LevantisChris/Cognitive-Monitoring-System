#!/usr/bin/env python
"""
Simple script to run tests for the get_screen_time_events_of_a_user function.

This script can be used to verify that the testing setup works correctly.
"""

import sys
import subprocess
import os

def check_dependencies():
    """Check if required testing dependencies are available."""
    try:
        import pytest
        print("✓ pytest is available")
        return True
    except ImportError:
        print("✗ pytest not found. Please install testing dependencies:")
        print("  pip install pytest pytest-mock pytest-cov")
        return False

def run_tests():
    """Run the database service tests."""
    if not check_dependencies():
        return False
    
    # Change to the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("\nRunning tests for get_screen_time_events_of_a_user function...")
    print("=" * 60)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_database_service.py::TestDatabaseServiceScreenTimeEvents",
            "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)