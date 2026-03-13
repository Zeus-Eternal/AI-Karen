"""
Simple test runner for Agent UI Service tests.
"""

import sys
import os
import unittest

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test module
from test_agent_ui_service import (
    TestAgentUIService,
    TestThreadManager,
    TestSessionStateManager,
    TestCopilotSafetyMiddleware
)

if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAgentUIService))
    suite.addTests(loader.loadTestsFromTestCase(TestThreadManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionStateManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCopilotSafetyMiddleware))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    print(f"\nTests run: {result.testsRun}")
    print(f"Tests failed: {len(result.failures)}")
    print(f"Tests errors: {len(result.errors)}")
    print(f"Success rate: {result.wasSuccessful()}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)