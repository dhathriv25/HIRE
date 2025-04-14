#!/usr/bin/env python3
"""
run_tests.py
"""

import unittest
import os
import sys
import time
from io import StringIO
from unittest.runner import TextTestResult

# Custom TestResult class to add spacing and messages after tests
class CustomTestResult(TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln("\n")
        self.stream.writeln("Test completed SUCCESSFULLY")
        self.stream.writeln("-" * 70)
        self.stream.writeln("\n")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.writeln("\n")
        self.stream.writeln("Test FAILED with an error")
        self.stream.writeln("-" * 70)
        self.stream.writeln("\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.writeln("\n")
        self.stream.writeln(" Test FAILED")
        self.stream.writeln("-" * 70)
        self.stream.writeln("\n")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.writeln("\n")
        self.stream.writeln(f"Test SKIPPED: {reason}")
        self.stream.writeln("-" * 70)
        self.stream.writeln("\n")

# Custom TestRunner that uses our CustomTestResult
class CustomTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return CustomTestResult(self.stream, self.descriptions, self.verbosity)


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
    
    # Use our custom test runner
    runner = CustomTestRunner(verbosity=2)
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
    print("="*70+"\n\n")
    
    # Return success if no failures or errors
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)