"""
Main CLI entry point for extension development tools.
"""

import argparse
import sys
from typing import List, Optional

from .commands.create import CreateCommand
from .commands.validate import ValidateCommand
from .commands.test import TestCommand
from .commands.package import PackageCommand
from .commands.dev_server import DevServerCommand


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="kari-ext",
        description="Kari Extension Development Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kari-ext create my-extension --template basic
  kari-ext validate ./my-extension
  kari-ext test ./my-extension
  kari-ext package ./my-extension
  kari-ext dev-server ./my-extension --watch
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser(
        "create", 
        help="Create a new extension from template"
    )
    CreateCommand.add_arguments(create_parser)
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", 
        help="Validate extension manifest and structure"
    )
    ValidateCommand.add_arguments(validate_parser)
    
    # Test command
    test_parser = subparsers.add_parser(
        "test", 
        help="Run extension tests"
    )
    TestCommand.add_arguments(test_parser)
    
    # Package command
    package_parser = subparsers.add_parser(
        "package", 
        help="Package extension for distribution"
    )
    PackageCommand.add_arguments(package_parser)
    
    # Dev server command
    dev_parser = subparsers.add_parser(
        "dev-server", 
        help="Start development server with hot reload"
    )
    DevServerCommand.add_arguments(dev_parser)
    
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    try:
        if parsed_args.command == "create":
            return CreateCommand.execute(parsed_args)
        elif parsed_args.command == "validate":
            return ValidateCommand.execute(parsed_args)
        elif parsed_args.command == "test":
            return TestCommand.execute(parsed_args)
        elif parsed_args.command == "package":
            return PackageCommand.execute(parsed_args)
        elif parsed_args.command == "dev-server":
            return DevServerCommand.execute(parsed_args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())