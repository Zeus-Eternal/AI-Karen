"""
Base command class for CLI commands.
"""

import argparse
from abc import ABC, abstractmethod
from typing import Any


class BaseCommand(ABC):
    """Base class for CLI commands."""
    
    @staticmethod
    @abstractmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser."""
        pass
    
    @staticmethod
    @abstractmethod
    def execute(args: argparse.Namespace) -> int:
        """Execute the command and return exit code."""
        pass
    
    @staticmethod
    def print_success(message: str) -> None:
        """Print a success message."""
        print(f"✅ {message}")
    
    @staticmethod
    def print_error(message: str) -> None:
        """Print an error message."""
        print(f"❌ {message}")
    
    @staticmethod
    def print_warning(message: str) -> None:
        """Print a warning message."""
        print(f"⚠️  {message}")
    
    @staticmethod
    def print_info(message: str) -> None:
        """Print an info message."""
        print(f"ℹ️  {message}")