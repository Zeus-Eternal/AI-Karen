#!/usr/bin/env python3
"""
Database Setup and Configuration Script.

Interactive script to help set up database connections for AI-Karen.
Supports MySQL (default), MongoDB, and Firestore.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str) -> None:
    """Print a styled header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-' * len(text)}{Colors.ENDC}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def prompt_choice(prompt: str, choices: List[str], default: Optional[str] = None) -> str:
    """
    Prompt user for a choice from a list.

    Args:
        prompt: Question to ask
        choices: List of valid choices
        default: Default choice if user presses Enter

    Returns:
        Selected choice
    """
    while True:
        print(f"\n{Colors.BOLD}{prompt}{Colors.ENDC}")
        for i, choice in enumerate(choices, 1):
            default_marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{default_marker}")

        choice_str = input(f"\nEnter choice [1-{len(choices)}]: ").strip()

        if not choice_str and default:
            return default

        try:
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(choices):
                return choices[choice_idx]
            else:
                print_error(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print_error("Please enter a valid number")


def prompt_input(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
    """
    Prompt user for input.

    Args:
        prompt: Question to ask
        default: Default value if user presses Enter
        required: Whether input is required

    Returns:
        User input
    """
    default_str = f" [{default}]" if default else ""
    required_str = " (required)" if required else " (optional)"

    while True:
        value = input(f"{prompt}{default_str}{required_str}: ").strip()

        if not value and default:
            return default

        if not value and not required:
            return ""

        if value:
            return value

        if required:
            print_error("This field is required. Please enter a value.")


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """
    Prompt user for yes/no answer.

    Args:
        prompt: Question to ask
        default: Default answer

    Returns:
        True for yes, False for no
    """
    default_str = " [Y/n]" if default else " [y/N]"
    while True:
        answer = input(f"{prompt}{default_str}: ").strip().lower()

        if not answer:
            return default

        if answer in ["y", "yes"]:
            return True
        elif answer in ["n", "no"]:
            return False
        else:
            print_error("Please answer 'y' or 'n'")


def setup_mysql() -> Dict[str, str]:
    """Set up MySQL configuration."""
    print_section("MySQL Configuration")
    print_info("MySQL is a popular open-source relational database.")

    config = {
        "DB_TYPE": "mysql",
        "MYSQL_HOST": prompt_input("MySQL host", default="localhost"),
        "MYSQL_PORT": prompt_input("MySQL port", default="3306"),
        "MYSQL_USER": prompt_input("MySQL username", default="root"),
        "MYSQL_PASSWORD": prompt_input("MySQL password", required=True),
        "MYSQL_DATABASE": prompt_input("Database name", default="ai_karen"),
        "MYSQL_POOL_SIZE": prompt_input("Connection pool size", default="10"),
        "MYSQL_MAX_OVERFLOW": prompt_input("Max pool overflow", default="20"),
    }

    # Ask about SSL
    if prompt_yes_no("Enable SSL/TLS?", default=False):
        config["MYSQL_SSL_CA"] = prompt_input("SSL CA certificate path", required=False)
        config["MYSQL_SSL_CERT"] = prompt_input("SSL client certificate path", required=False)
        config["MYSQL_SSL_KEY"] = prompt_input("SSL client key path", required=False)

    return config


def setup_mongodb() -> Dict[str, str]:
    """Set up MongoDB configuration."""
    print_section("MongoDB Configuration")
    print_info("MongoDB is a popular NoSQL document database.")

    config = {
        "DB_TYPE": "mongodb",
        "MONGO_HOST": prompt_input("MongoDB host", default="localhost"),
        "MONGO_PORT": prompt_input("MongoDB port", default="27017"),
        "MONGO_DATABASE": prompt_input("Database name", default="ai_karen"),
    }

    # Ask about authentication
    if prompt_yes_no("Enable authentication?", default=True):
        config["MONGO_USER"] = prompt_input("MongoDB username", default="admin")
        config["MONGO_PASSWORD"] = prompt_input("MongoDB password", required=True)
        config["MONGO_AUTH_SOURCE"] = prompt_input("Auth source", default="admin")

    # Connection pool settings
    config["MONGO_MAX_POOL_SIZE"] = prompt_input("Max connection pool size", default="100")
    config["MONGO_MIN_POOL_SIZE"] = prompt_input("Min connection pool size", default="10")

    # Ask about replica set
    if prompt_yes_no("Using replica set?", default=False):
        config["MONGO_REPLICA_SET"] = prompt_input("Replica set name", required=True)

    # Ask about SSL
    if prompt_yes_no("Enable SSL/TLS?", default=False):
        config["MONGO_SSL"] = "true"
        config["MONGO_SSL_CA_CERTS"] = prompt_input("SSL CA certificate path", required=False)

    return config


def setup_firestore() -> Dict[str, str]:
    """Set up Firestore configuration."""
    print_section("Firestore Configuration")
    print_info("Google Cloud Firestore is a NoSQL document database built for automatic scaling.")

    # Ask about emulator mode
    use_emulator = prompt_yes_no("Use Firestore emulator (local development)?", default=False)

    if use_emulator:
        config = {
            "DB_TYPE": "firestore",
            "FIRESTORE_PROJECT_ID": prompt_input("GCP Project ID", default="demo-project"),
            "FIRESTORE_USE_EMULATOR": "true",
            "FIRESTORE_EMULATOR_HOST": prompt_input("Emulator host", default="localhost"),
            "FIRESTORE_EMULATOR_PORT": prompt_input("Emulator port", default="8080"),
        }
    else:
        config = {
            "DB_TYPE": "firestore",
            "FIRESTORE_PROJECT_ID": prompt_input("GCP Project ID", required=True),
        }

        # Ask about credentials
        cred_choice = prompt_choice(
            "How do you want to provide credentials?",
            ["Service account JSON file path", "Service account JSON content", "Default application credentials"],
            default="Service account JSON file path"
        )

        if cred_choice == "Service account JSON file path":
            config["FIRESTORE_CREDENTIALS_PATH"] = prompt_input(
                "Path to service account JSON file", required=True
            )
        elif cred_choice == "Service account JSON content":
            print_warning("You'll need to paste the entire JSON content (in one line)")
            config["FIRESTORE_CREDENTIALS_JSON"] = prompt_input(
                "Service account JSON content", required=True
            )
        # else: use default application credentials (no config needed)

        # Database ID
        config["FIRESTORE_DATABASE_ID"] = prompt_input(
            "Firestore database ID", default="(default)"
        )

    return config


def write_env_file(config: Dict[str, str], env_file_path: Path) -> None:
    """
    Write configuration to .env file.

    Args:
        config: Configuration dictionary
        env_file_path: Path to .env file
    """
    lines = [
        "# Multi-Database Configuration",
        f"# Generated by setup_database.py",
        f"# Database Type: {config.get('DB_TYPE', 'unknown')}",
        "",
    ]

    for key, value in config.items():
        if value:  # Only write non-empty values
            lines.append(f"{key}={value}")

    content = "\n".join(lines) + "\n"

    # Backup existing file if it exists
    if env_file_path.exists():
        backup_path = env_file_path.with_suffix(".env.backup")
        env_file_path.rename(backup_path)
        print_warning(f"Existing .env file backed up to: {backup_path}")

    # Write new file
    env_file_path.write_text(content)
    print_success(f"Configuration written to: {env_file_path}")


def test_connection(config: Dict[str, str]) -> bool:
    """
    Test database connection.

    Args:
        config: Configuration dictionary

    Returns:
        True if connection successful, False otherwise
    """
    print_section("Testing Database Connection")

    db_type = config.get("DB_TYPE", "unknown")

    # Set environment variables temporarily
    for key, value in config.items():
        os.environ[key] = value

    try:
        if db_type == "mysql":
            return test_mysql_connection(config)
        elif db_type == "mongodb":
            return test_mongodb_connection(config)
        elif db_type == "firestore":
            return test_firestore_connection(config)
        else:
            print_error(f"Unknown database type: {db_type}")
            return False
    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False


def test_mysql_connection(config: Dict[str, str]) -> bool:
    """Test MySQL connection."""
    try:
        import pymysql
    except ImportError:
        print_error("pymysql is not installed. Run: pip install pymysql")
        return False

    try:
        connection = pymysql.connect(
            host=config["MYSQL_HOST"],
            port=int(config["MYSQL_PORT"]),
            user=config["MYSQL_USER"],
            password=config["MYSQL_PASSWORD"],
            database=config["MYSQL_DATABASE"],
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print_success(f"Connected to MySQL {version}")

        connection.close()
        return True

    except Exception as e:
        print_error(f"MySQL connection failed: {e}")
        return False


def test_mongodb_connection(config: Dict[str, str]) -> bool:
    """Test MongoDB connection."""
    try:
        from pymongo import MongoClient
    except ImportError:
        print_error("pymongo is not installed. Run: pip install pymongo")
        return False

    try:
        client_kwargs = {
            "host": config["MONGO_HOST"],
            "port": int(config["MONGO_PORT"]),
        }

        if "MONGO_USER" in config and config["MONGO_USER"]:
            client_kwargs["username"] = config["MONGO_USER"]
            client_kwargs["password"] = config["MONGO_PASSWORD"]
            client_kwargs["authSource"] = config.get("MONGO_AUTH_SOURCE", "admin")

        client = MongoClient(**client_kwargs, serverSelectionTimeoutMS=5000)

        # Test connection
        info = client.server_info()
        version = info["version"]
        print_success(f"Connected to MongoDB {version}")

        client.close()
        return True

    except Exception as e:
        print_error(f"MongoDB connection failed: {e}")
        return False


def test_firestore_connection(config: Dict[str, str]) -> bool:
    """Test Firestore connection."""
    try:
        from google.cloud import firestore
    except ImportError:
        print_error("google-cloud-firestore is not installed. Run: pip install google-cloud-firestore")
        return False

    try:
        use_emulator = config.get("FIRESTORE_USE_EMULATOR") == "true"

        if use_emulator:
            os.environ["FIRESTORE_EMULATOR_HOST"] = f"{config['FIRESTORE_EMULATOR_HOST']}:{config['FIRESTORE_EMULATOR_PORT']}"
            client = firestore.Client(project=config["FIRESTORE_PROJECT_ID"])
            print_success(f"Connected to Firestore emulator at {os.environ['FIRESTORE_EMULATOR_HOST']}")
        else:
            # Try to create client
            client_kwargs = {"project": config["FIRESTORE_PROJECT_ID"]}

            if "FIRESTORE_CREDENTIALS_PATH" in config:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    config["FIRESTORE_CREDENTIALS_PATH"]
                )
                client_kwargs["credentials"] = credentials

            client = firestore.Client(**client_kwargs)
            print_success(f"Connected to Firestore project: {config['FIRESTORE_PROJECT_ID']}")

        # Test by listing collections (limit to 1)
        list(client.collections(page_size=1))

        return True

    except Exception as e:
        print_error(f"Firestore connection failed: {e}")
        return False


def print_next_steps(db_type: str) -> None:
    """Print next steps after configuration."""
    print_section("Next Steps")

    if db_type == "mysql":
        print_info("1. Ensure MySQL server is running")
        print_info("2. Create the database if it doesn't exist:")
        print(f"   {Colors.CYAN}CREATE DATABASE ai_karen;{Colors.ENDC}")
        print_info("3. Install Python dependencies:")
        print(f"   {Colors.CYAN}pip install sqlalchemy pymysql aiomysql{Colors.ENDC}")

    elif db_type == "mongodb":
        print_info("1. Ensure MongoDB server is running")
        print_info("2. Install Python dependencies:")
        print(f"   {Colors.CYAN}pip install pymongo motor{Colors.ENDC}")
        print_info("3. Consider enabling authentication in production")

    elif db_type == "firestore":
        print_info("1. Install Python dependencies:")
        print(f"   {Colors.CYAN}pip install google-cloud-firestore{Colors.ENDC}")
        print_info("2. For emulator: Start Firestore emulator:")
        print(f"   {Colors.CYAN}gcloud emulators firestore start --host-port=localhost:8080{Colors.ENDC}")
        print_info("3. For production: Ensure service account has Firestore permissions")

    print_info("\n4. Load configuration in your application:")
    print(f"   {Colors.CYAN}from ai_karen_engine.database.multi_db_config import load_multi_database_config{Colors.ENDC}")
    print(f"   {Colors.CYAN}from ai_karen_engine.database.multi_db_factory import DatabaseConnectionFactory{Colors.ENDC}")
    print(f"   {Colors.CYAN}config = load_multi_database_config(){Colors.ENDC}")
    print(f"   {Colors.CYAN}factory = DatabaseConnectionFactory(config){Colors.ENDC}")


def main():
    """Main setup flow."""
    print_header("AI-Karen Database Setup")
    print(f"{Colors.BOLD}Welcome to the AI-Karen database configuration wizard!{Colors.ENDC}")
    print("This will help you set up your database connection.\n")

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_file_path = project_root / ".env.database"

    # Choose database type
    db_type = prompt_choice(
        "Which database would you like to use?",
        ["MySQL (Recommended - Default)", "MongoDB (NoSQL)", "Firestore (Google Cloud NoSQL)"],
        default="MySQL (Recommended - Default)"
    )

    # Set up configuration based on choice
    if "MySQL" in db_type:
        config = setup_mysql()
    elif "MongoDB" in db_type:
        config = setup_mongodb()
    elif "Firestore" in db_type:
        config = setup_firestore()
    else:
        print_error("Invalid database type selected")
        sys.exit(1)

    # Write configuration
    print_section("Saving Configuration")
    write_env_file(config, env_file_path)

    # Test connection
    if prompt_yes_no("\nWould you like to test the database connection?", default=True):
        if test_connection(config):
            print_success("\nDatabase setup completed successfully!")
        else:
            print_warning("\nDatabase configuration saved, but connection test failed.")
            print_warning("Please check your settings and ensure the database server is running.")

    # Print next steps
    print_next_steps(config["DB_TYPE"])

    print(f"\n{Colors.GREEN}{Colors.BOLD}Setup complete!{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nSetup failed: {e}")
        sys.exit(1)
