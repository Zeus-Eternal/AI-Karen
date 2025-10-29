#!/usr/bin/env python3
"""
Comprehensive Validation Runner
Quick script to run all comprehensive tests for the intelligent response optimization system.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run comprehensive validation tests."""
    print("🚀 Starting Comprehensive Validation for Intelligent Response Optimization")
    print("=" * 70)
    
    # Change to the comprehensive tests directory
    test_dir = Path("tests/comprehensive")
    
    if not test_dir.exists():
        print("❌ Error: Comprehensive tests directory not found!")
        print("   Expected: tests/comprehensive/")
        return 1
    
    # Run the comprehensive test runner
    try:
        cmd = [sys.executable, "tests/comprehensive/run_comprehensive_tests.py"]
        
        # Add any command line arguments passed to this script
        if len(sys.argv) > 1:
            cmd.extend(sys.argv[1:])
        
        print(f"📋 Executing: {' '.join(cmd)}")
        print()
        
        # Run the tests
        result = subprocess.run(cmd, cwd=".")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running validation: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)