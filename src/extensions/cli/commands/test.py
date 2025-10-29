"""
Test command for running extension tests.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .base import BaseCommand


class TestCommand(BaseCommand):
    """Command to run extension tests."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add test command arguments."""
        parser.add_argument(
            "path",
            type=Path,
            help="Path to extension directory"
        )
        parser.add_argument(
            "--pattern", "-p",
            default="test_*.py",
            help="Test file pattern (default: test_*.py)"
        )
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Verbose test output"
        )
        parser.add_argument(
            "--coverage",
            action="store_true",
            help="Run tests with coverage reporting"
        )
        parser.add_argument(
            "--parallel", "-j",
            type=int,
            help="Run tests in parallel (number of workers)"
        )
        parser.add_argument(
            "--filter", "-k",
            help="Filter tests by keyword expression"
        )
        parser.add_argument(
            "--markers", "-m",
            help="Run tests with specific markers"
        )
        parser.add_argument(
            "--output-format",
            choices=["text", "junit", "json"],
            default="text",
            help="Test output format"
        )
        parser.add_argument(
            "--fail-fast", "-x",
            action="store_true",
            help="Stop on first test failure"
        )
    
    @staticmethod
    def execute(args: argparse.Namespace) -> int:
        """Execute the test command."""
        extension_path = args.path
        
        if not extension_path.exists():
            TestCommand.print_error(f"Extension path '{extension_path}' does not exist")
            return 1
        
        if not extension_path.is_dir():
            TestCommand.print_error(f"Extension path '{extension_path}' is not a directory")
            return 1
        
        # Check if tests directory exists
        tests_dir = extension_path / "tests"
        if not tests_dir.exists():
            TestCommand.print_error("No tests directory found")
            TestCommand.print_info("Create tests with: mkdir tests && touch tests/__init__.py")
            return 1
        
        try:
            # Run tests
            return TestCommand._run_tests(extension_path, args)
            
        except Exception as e:
            TestCommand.print_error(f"Test execution failed: {e}")
            return 1
    
    @staticmethod
    def _run_tests(extension_path: Path, args: argparse.Namespace) -> int:
        """Run the test suite."""
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test directory
        cmd.append(str(extension_path / "tests"))
        
        # Add pattern
        cmd.extend(["--tb=short"])
        
        # Add verbosity
        if args.verbose:
            cmd.append("-v")
        
        # Add coverage
        if args.coverage:
            cmd.extend([
                "--cov=" + str(extension_path),
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov"
            ])
        
        # Add parallel execution
        if args.parallel:
            cmd.extend(["-n", str(args.parallel)])
        
        # Add filter
        if args.filter:
            cmd.extend(["-k", args.filter])
        
        # Add markers
        if args.markers:
            cmd.extend(["-m", args.markers])
        
        # Add output format
        if args.output_format == "junit":
            cmd.extend(["--junit-xml=test-results.xml"])
        elif args.output_format == "json":
            cmd.extend(["--json-report", "--json-report-file=test-results.json"])
        
        # Add fail fast
        if args.fail_fast:
            cmd.append("-x")
        
        TestCommand.print_info(f"Running tests in {extension_path}")
        TestCommand.print_info(f"Command: {' '.join(cmd)}")
        
        # Run the command
        try:
            result = subprocess.run(
                cmd,
                cwd=extension_path,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                TestCommand.print_success("All tests passed!")
            else:
                TestCommand.print_error("Some tests failed")
            
            return result.returncode
            
        except FileNotFoundError:
            TestCommand.print_error("pytest not found. Install with: pip install pytest")
            return 1
        except subprocess.CalledProcessError as e:
            TestCommand.print_error(f"Test execution failed: {e}")
            return e.returncode
    
    @staticmethod
    def _check_test_dependencies() -> List[str]:
        """Check for required test dependencies."""
        missing = []
        
        try:
            import pytest
        except ImportError:
            missing.append("pytest")
        
        try:
            import pytest_asyncio
        except ImportError:
            missing.append("pytest-asyncio")
        
        return missing
    
    @staticmethod
    def _suggest_test_setup(extension_path: Path) -> None:
        """Suggest test setup for the extension."""
        TestCommand.print_info("To set up testing for this extension:")
        print("1. Create a tests directory:")
        print(f"   mkdir {extension_path}/tests")
        print(f"   touch {extension_path}/tests/__init__.py")
        print()
        print("2. Install test dependencies:")
        print("   pip install pytest pytest-asyncio")
        print()
        print("3. Create a basic test file:")
        print(f"   touch {extension_path}/tests/test_extension.py")
        print()
        print("4. Run tests:")
        print(f"   kari-ext test {extension_path}")
    
    @staticmethod
    def _create_sample_test(extension_path: Path) -> None:
        """Create a sample test file."""
        tests_dir = extension_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        (tests_dir / "__init__.py").touch()
        
        # Create sample test
        extension_name = extension_path.name
        class_name = "".join(word.capitalize() for word in extension_name.split("-"))
        
        test_content = f'''"""
Sample tests for {extension_name} extension.
"""

import pytest
from unittest.mock import Mock


class Test{class_name}Extension:
    """Test cases for the extension."""
    
    def test_extension_creation(self):
        """Test that extension can be created."""
        # Add your test logic here
        assert True
    
    @pytest.mark.asyncio
    async def test_extension_initialization(self):
        """Test extension initialization."""
        # Add your async test logic here
        assert True
    
    def test_extension_configuration(self):
        """Test extension configuration."""
        # Add configuration tests here
        assert True
'''
        
        with open(tests_dir / "test_extension.py", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        TestCommand.print_success(f"Created sample test file: {tests_dir}/test_extension.py")