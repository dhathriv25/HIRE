#!/usr/bin/env python3
"""
Simplified test runner for HIRE platform

Usage:
  python simplified_run_tests.py
"""

import unittest
import os
import sys
import time

def run_tests():
    """Run all tests in the current directory"""
    start_time = time.time()
    
    # Get the current directory (where this script is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the parent directory to the path so tests can import app modules
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(current_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print(f"TEST SUMMARY:")
    print(f"  Ran {result.testsRun} tests in {duration:.2f} seconds")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print("="*70)
    
    # Return success if no failures or errors
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

