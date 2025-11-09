"""
Enhanced Error Formatting Utilities
Provides distinctive, user-friendly error messages with visual indicators and solutions.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """Error severity levels with visual indicators."""
    CRITICAL = "🚨"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    SUCCESS = "✅"


class ErrorCategory(Enum):
    """Error categories for better organization."""
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass
class ErrorSolution:
    """Represents a solution to an error."""
    description: str
    commands: List[str] = None
    links: List[str] = None
    priority: int = 1  # 1 = highest priority


@dataclass
class FormattedError:
    """A formatted error with enhanced information."""
    severity: ErrorSeverity
    category: ErrorCategory
    title: str
    description: str
    original_error: str
    solutions: List[ErrorSolution]
    context: Dict[str, Any] = None


class ErrorFormatter:
    """Enhanced error formatter with visual indicators and solutions."""
    
    # Common error patterns and their solutions
    ERROR_PATTERNS = {
        "Can't find model 'en_core_web_sm'": {
            "category": ErrorCategory.DEPENDENCY,
            "severity": ErrorSeverity.ERROR,
            "title": "spaCy Language Model Missing",
            "description": "The required spaCy English language model is not installed.",
            "solutions": [
                ErrorSolution(
                    description="Install the spaCy English model",
                    commands=[
                        "source .env_kari/bin/activate",
                        "python -m spacy download en_core_web_sm"
                    ],
                    priority=1
                ),
                ErrorSolution(
                    description="Alternative: Install a different model",
                    commands=[
                        "python -m spacy download en_core_web_md"
                    ],
                    priority=2
                )
            ]
        },
        
        "Could not parse SQLAlchemy URL": {
            "category": ErrorCategory.DATABASE,
            "severity": ErrorSeverity.CRITICAL,
            "title": "Database Configuration Error",
            "description": "The database URL format is invalid or missing.",
            "solutions": [
                ErrorSolution(
                    description="Check your .env file for DATABASE_URL",
                    commands=[
                        "grep DATABASE_URL .env",
                        "# Should be: postgresql://user:pass@host:port/dbname"
                    ],
                    priority=1
                ),
                ErrorSolution(
                    description="Start PostgreSQL service",
                    commands=[
                        "docker compose up -d postgres"
                    ],
                    priority=2
                )
            ]
        },
        
        "Connection refused": {
            "category": ErrorCategory.NETWORK,
            "severity": ErrorSeverity.ERROR,
            "title": "Service Connection Failed",
            "description": "Cannot connect to the required service.",
            "solutions": [
                ErrorSolution(
                    description="Check if the service is running",
                    commands=[
                        "docker ps",
                        "docker compose ps"
                    ],
                    priority=1
                ),
                ErrorSolution(
                    description="Start the required services",
                    commands=[
                        "docker compose up -d"
                    ],
                    priority=2
                )
            ]
        },
        
        "ModuleNotFoundError": {
            "category": ErrorCategory.DEPENDENCY,
            "severity": ErrorSeverity.ERROR,
            "title": "Python Module Missing",
            "description": "A required Python package is not installed.",
            "solutions": [
                ErrorSolution(
                    description="Install missing dependencies",
                    commands=[
                        "source .env_kari/bin/activate",
                        "pip install -r requirements.txt"
                    ],
                    priority=1
                ),
                ErrorSolution(
                    description="Reinstall the virtual environment",
                    commands=[
                        "rm -rf .env_kari",
                        "python -m venv .env_kari",
                        "source .env_kari/bin/activate",
                        "pip install -r requirements.txt"
                    ],
                    priority=2
                )
            ]
        }
    }
    
    @classmethod
    def format_error(
        cls, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        custom_solutions: Optional[List[ErrorSolution]] = None
    ) -> FormattedError:
        """
        Format an error with enhanced information and solutions.
        
        Args:
            error: The original exception
            context: Additional context information
            custom_solutions: Custom solutions to add
            
        Returns:
            FormattedError with enhanced information
        """
        error_str = str(error)
        
        # Find matching pattern
        matched_pattern = None
        for pattern, config in cls.ERROR_PATTERNS.items():
            if pattern in error_str:
                matched_pattern = config
                break
        
        if matched_pattern:
            formatted = FormattedError(
                severity=matched_pattern["severity"],
                category=matched_pattern["category"],
                title=matched_pattern["title"],
                description=matched_pattern["description"],
                original_error=error_str,
                solutions=matched_pattern["solutions"].copy(),
                context=context or {}
            )
        else:
            # Generic error formatting
            formatted = FormattedError(
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                title="Unexpected Error",
                description="An unexpected error occurred.",
                original_error=error_str,
                solutions=[
                    ErrorSolution(
                        description="Check the logs for more details",
                        commands=["tail -f logs/app.log"],
                        priority=1
                    )
                ],
                context=context or {}
            )
        
        # Add custom solutions if provided
        if custom_solutions:
            formatted.solutions.extend(custom_solutions)
            # Sort by priority
            formatted.solutions.sort(key=lambda x: x.priority)
        
        return formatted
    
    @classmethod
    def format_message(cls, formatted_error: FormattedError) -> str:
        """
        Convert a FormattedError to a user-friendly message.
        
        Args:
            formatted_error: The formatted error object
            
        Returns:
            Formatted error message string
        """
        lines = []
        
        # Header with severity icon
        lines.append(f"{formatted_error.severity.value} {formatted_error.title}")
        lines.append("=" * (len(formatted_error.title) + 3))
        lines.append("")
        
        # Description
        lines.append(f"📝 Description: {formatted_error.description}")
        lines.append("")
        
        # Original error (if different from description)
        if formatted_error.original_error != formatted_error.description:
            lines.append(f"🔍 Technical Details: {formatted_error.original_error}")
            lines.append("")
        
        # Solutions
        if formatted_error.solutions:
            lines.append("🔧 Solutions:")
            for i, solution in enumerate(formatted_error.solutions, 1):
                lines.append(f"   {i}. {solution.description}")
                if solution.commands:
                    lines.append("      Commands:")
                    for cmd in solution.commands:
                        lines.append(f"        $ {cmd}")
                if solution.links:
                    lines.append("      Links:")
                    for link in solution.links:
                        lines.append(f"        🔗 {link}")
                lines.append("")
        
        # Context information
        if formatted_error.context:
            lines.append("📊 Context:")
            for key, value in formatted_error.context.items():
                lines.append(f"   • {key}: {value}")
            lines.append("")
        
        # Category and severity info
        lines.append(f"🏷️  Category: {formatted_error.category.value}")
        lines.append(f"⚡ Severity: {formatted_error.severity.name}")
        
        return "\n".join(lines)
    
    @classmethod
    def log_formatted_error(
        cls, 
        logger: logging.Logger, 
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        custom_solutions: Optional[List[ErrorSolution]] = None
    ):
        """
        Log a formatted error with enhanced information.
        
        Args:
            logger: Logger instance to use
            error: The original exception
            context: Additional context information
            custom_solutions: Custom solutions to add
        """
        formatted = cls.format_error(error, context, custom_solutions)
        message = cls.format_message(formatted)
        
        # Log at appropriate level based on severity
        if formatted.severity == ErrorSeverity.CRITICAL:
            logger.critical(message)
        elif formatted.severity == ErrorSeverity.ERROR:
            logger.error(message)
        elif formatted.severity == ErrorSeverity.WARNING:
            logger.warning(message)
        else:
            logger.info(message)
    
    @classmethod
    def add_error_pattern(
        cls,
        pattern: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        title: str,
        description: str,
        solutions: List[ErrorSolution]
    ):
        """
        Add a new error pattern to the formatter.
        
        Args:
            pattern: Error pattern to match
            category: Error category
            severity: Error severity
            title: Error title
            description: Error description
            solutions: List of solutions
        """
        cls.ERROR_PATTERNS[pattern] = {
            "category": category,
            "severity": severity,
            "title": title,
            "description": description,
            "solutions": solutions
        }


# Convenience functions for common use cases
def log_dependency_error(logger: logging.Logger, error: Exception, package_name: str):
    """Log a dependency-related error with installation instructions."""
    context = {"package": package_name}
    solutions = [
        ErrorSolution(
            description=f"Install {package_name}",
            commands=[f"pip install {package_name}"],
            priority=1
        )
    ]
    ErrorFormatter.log_formatted_error(logger, error, context, solutions)


def log_service_error(logger: logging.Logger, error: Exception, service_name: str):
    """Log a service-related error with startup instructions."""
    context = {"service": service_name}
    solutions = [
        ErrorSolution(
            description=f"Start {service_name} service",
            commands=[f"docker compose up -d {service_name}"],
            priority=1
        )
    ]
    ErrorFormatter.log_formatted_error(logger, error, context, solutions)


def log_config_error(logger: logging.Logger, error: Exception, config_file: str):
    """Log a configuration-related error with fix instructions."""
    context = {"config_file": config_file}
    solutions = [
        ErrorSolution(
            description=f"Check {config_file} configuration",
            commands=[f"cat {config_file}", f"nano {config_file}"],
            priority=1
        )
    ]
    ErrorFormatter.log_formatted_error(logger, error, context, solutions)