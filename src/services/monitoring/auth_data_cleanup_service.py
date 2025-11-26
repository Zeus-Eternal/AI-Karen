"""
Authentication Data Cleanup Service

Service to clean demo accounts and prepare authentication data for production.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ...internal..core.services.base import BaseService, ServiceConfig


class AuthDataCleanupService(BaseService):
    """
    Service for cleaning authentication data for production deployment.
    
    Removes demo accounts, validates production data, and creates backups.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if config is None:
            config = ServiceConfig(
                name="auth_data_cleanup",
                enabled=True,
                config={
                    "users_file": "data/users.json",
                    "backup_directory": "backups/auth_cleanup",
                    "demo_account_patterns": [
                        "admin@example.com",
                        "test@example.com", 
                        "demo@example.com",
                        "user@example.com",
                        "dev@example.com"
                    ],
                    "preserve_accounts": [
                        "admin@kari.ai"  # Keep legitimate admin accounts
                    ]
                }
            )
        
        super().__init__(config)
        self.users_file = Path(config.config.get("users_file", "data/users.json"))
        self.backup_directory = Path(config.config.get("backup_directory", "backups/auth_cleanup"))
        self.demo_patterns = config.config.get("demo_account_patterns", [])
        self.preserve_accounts = config.config.get("preserve_accounts", [])
        
        self.cleanup_report = {
            "timestamp": None,
            "original_user_count": 0,
            "cleaned_user_count": 0,
            "removed_accounts": [],
            "preserved_accounts": [],
            "validation_issues": [],
            "backup_created": None
        }
    
    async def initialize(self) -> None:
        """Initialize the cleanup service."""
        self.logger.info("Initializing Auth Data Cleanup Service")
        
        # Create backup directory
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Cleanup service initialized. Backup directory: {self.backup_directory}")
    
    async def start(self) -> None:
        """Start the cleanup service."""
        self.logger.info("Auth Data Cleanup Service started")
    
    async def stop(self) -> None:
        """Stop the cleanup service."""
        self.logger.info("Auth Data Cleanup Service stopped")
    
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            # Check if users file exists and is readable
            if self.users_file.exists():
                self.users_file.read_text()
            
            # Check if backup directory is writable
            test_file = self.backup_directory / "health_check.tmp"
            test_file.write_text("health check")
            test_file.unlink()
            
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _create_backup(self) -> Path:
        """Create a backup of the current users file."""
        if not self.users_file.exists():
            self.logger.warning("Users file does not exist, no backup needed")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_directory / f"users_backup_{timestamp}.json"
        
        shutil.copy2(self.users_file, backup_path)
        self.logger.info(f"Created backup: {backup_path}")
        
        return backup_path
    
    def _is_demo_account(self, email: str) -> bool:
        """Check if an email is a demo account that should be removed."""
        email_lower = email.lower()
        
        # Check against demo patterns
        for pattern in self.demo_patterns:
            if pattern.lower() == email_lower:
                return True
        
        # Check for common demo patterns
        demo_indicators = [
            "example.com",
            "test.com",
            "demo.com",
            "localhost"
        ]
        
        for indicator in demo_indicators:
            if indicator in email_lower:
                return True
        
        return False
    
    def _should_preserve_account(self, email: str) -> bool:
        """Check if an account should be preserved even if it looks like a demo."""
        return email.lower() in [acc.lower() for acc in self.preserve_accounts]
    
    def _validate_user_data(self, email: str, user_data: Dict[str, Any]) -> List[str]:
        """Validate user data and return list of issues."""
        issues = []
        
        # Required fields
        required_fields = ["user_id", "email", "password_hash", "full_name", "roles"]
        for field in required_fields:
            if field not in user_data:
                issues.append(f"Missing required field: {field}")
            elif not user_data[field]:
                issues.append(f"Empty required field: {field}")
        
        # Email validation
        if user_data.get("email") != email:
            issues.append(f"Email mismatch: key={email}, data={user_data.get('email')}")
        
        # Password hash validation
        password_hash = user_data.get("password_hash", "")
        if len(password_hash) < 32:  # Minimum reasonable hash length
            issues.append("Password hash appears too short or invalid")
        
        # Roles validation
        roles = user_data.get("roles", [])
        if not isinstance(roles, list) or len(roles) == 0:
            issues.append("Roles must be a non-empty list")
        
        # Check for placeholder values
        placeholder_indicators = ["test", "demo", "example", "placeholder", "dummy"]
        for field in ["full_name", "user_id"]:
            value = str(user_data.get(field, "")).lower()
            if any(indicator in value for indicator in placeholder_indicators):
                issues.append(f"Field '{field}' contains placeholder value: {user_data.get(field)}")
        
        return issues
    
    async def clean_demo_accounts(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean demo accounts from the users file.
        
        Args:
            dry_run: If True, don't actually modify files, just report what would be done
            
        Returns:
            Cleanup report with details of what was done
        """
        self.logger.info(f"Starting auth data cleanup (dry_run={dry_run})")
        
        # Initialize report
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "original_user_count": 0,
            "cleaned_user_count": 0,
            "removed_accounts": [],
            "preserved_accounts": [],
            "validation_issues": [],
            "backup_created": None,
            "dry_run": dry_run
        }
        
        # Check if users file exists
        if not self.users_file.exists():
            self.logger.warning("Users file does not exist")
            self.cleanup_report["validation_issues"].append("Users file does not exist")
            return self.cleanup_report
        
        # Create backup (even for dry run, for safety)
        backup_path = self._create_backup()
        if backup_path:
            self.cleanup_report["backup_created"] = str(backup_path)
        
        # Load current users
        try:
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load users file: {e}")
            self.cleanup_report["validation_issues"].append(f"Failed to load users file: {e}")
            return self.cleanup_report
        
        self.cleanup_report["original_user_count"] = len(users_data)
        
        # Process each user
        cleaned_users = {}
        
        for email, user_data in users_data.items():
            # Validate user data
            validation_issues = self._validate_user_data(email, user_data)
            if validation_issues:
                self.cleanup_report["validation_issues"].extend([
                    f"{email}: {issue}" for issue in validation_issues
                ])
            
            # Check if this is a demo account
            if self._is_demo_account(email):
                if self._should_preserve_account(email):
                    # Preserve this account even though it looks like demo
                    cleaned_users[email] = user_data
                    self.cleanup_report["preserved_accounts"].append({
                        "email": email,
                        "reason": "explicitly preserved",
                        "full_name": user_data.get("full_name", ""),
                        "roles": user_data.get("roles", [])
                    })
                    self.logger.info(f"Preserved account: {email} (explicitly preserved)")
                else:
                    # Remove demo account
                    self.cleanup_report["removed_accounts"].append({
                        "email": email,
                        "reason": "demo account",
                        "full_name": user_data.get("full_name", ""),
                        "roles": user_data.get("roles", [])
                    })
                    self.logger.info(f"Removed demo account: {email}")
            else:
                # Keep production account
                cleaned_users[email] = user_data
                self.cleanup_report["preserved_accounts"].append({
                    "email": email,
                    "reason": "production account",
                    "full_name": user_data.get("full_name", ""),
                    "roles": user_data.get("roles", [])
                })
        
        self.cleanup_report["cleaned_user_count"] = len(cleaned_users)
        
        # Save cleaned data (unless dry run)
        if not dry_run:
            try:
                with open(self.users_file, 'w') as f:
                    json.dump(cleaned_users, f, indent=2)
                self.logger.info(f"Saved cleaned users file with {len(cleaned_users)} users")
            except Exception as e:
                self.logger.error(f"Failed to save cleaned users file: {e}")
                self.cleanup_report["validation_issues"].append(f"Failed to save cleaned users file: {e}")
        else:
            self.logger.info("Dry run - no files were modified")
        
        # Log summary
        removed_count = len(self.cleanup_report["removed_accounts"])
        preserved_count = len(self.cleanup_report["preserved_accounts"])
        
        self.logger.info(f"Cleanup completed: {removed_count} accounts removed, {preserved_count} accounts preserved")
        
        return self.cleanup_report
    
    async def validate_production_data(self) -> Dict[str, Any]:
        """
        Validate that the current user data is ready for production.
        
        Returns:
            Validation report
        """
        self.logger.info("Validating production authentication data")
        
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "is_production_ready": False,
            "total_users": 0,
            "admin_users": 0,
            "active_users": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Check if users file exists
        if not self.users_file.exists():
            validation_report["issues"].append("Users file does not exist")
            validation_report["recommendations"].append("Run first-run setup to create initial admin user")
            return validation_report
        
        # Load users
        try:
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
        except Exception as e:
            validation_report["issues"].append(f"Failed to load users file: {e}")
            return validation_report
        
        validation_report["total_users"] = len(users_data)
        
        # Validate each user
        admin_count = 0
        active_count = 0
        
        for email, user_data in users_data.items():
            # Check for demo accounts
            if self._is_demo_account(email) and not self._should_preserve_account(email):
                validation_report["issues"].append(f"Demo account found: {email}")
            
            # Validate user data
            user_issues = self._validate_user_data(email, user_data)
            validation_report["issues"].extend([f"{email}: {issue}" for issue in user_issues])
            
            # Count admin users
            roles = user_data.get("roles", [])
            if "admin" in roles or "super_admin" in roles:
                admin_count += 1
            
            # Count active users
            if user_data.get("is_active", False):
                active_count += 1
        
        validation_report["admin_users"] = admin_count
        validation_report["active_users"] = active_count
        
        # Check for critical issues
        if admin_count == 0:
            validation_report["issues"].append("No admin users found")
            validation_report["recommendations"].append("Create at least one admin user")
        
        if active_count == 0:
            validation_report["issues"].append("No active users found")
            validation_report["recommendations"].append("Ensure at least one user is active")
        
        # Determine if production ready
        critical_issues = [
            issue for issue in validation_report["issues"]
            if any(keyword in issue.lower() for keyword in ["demo account", "no admin", "no active"])
        ]
        
        validation_report["is_production_ready"] = len(critical_issues) == 0
        
        if validation_report["is_production_ready"]:
            validation_report["recommendations"].append("Authentication data appears ready for production")
        else:
            validation_report["recommendations"].append("Address critical issues before production deployment")
        
        self.logger.info(f"Validation completed: {'READY' if validation_report['is_production_ready'] else 'NOT READY'}")
        
        return validation_report
    
    def generate_cleanup_report(self) -> str:
        """Generate a human-readable cleanup report."""
        if not self.cleanup_report.get("timestamp"):
            return "No cleanup has been performed yet."
        
        report_lines = [
            "Authentication Data Cleanup Report",
            "=" * 40,
            f"Timestamp: {self.cleanup_report['timestamp']}",
            f"Dry Run: {self.cleanup_report.get('dry_run', False)}",
            "",
            "Summary:",
            f"  Original users: {self.cleanup_report['original_user_count']}",
            f"  Cleaned users: {self.cleanup_report['cleaned_user_count']}",
            f"  Removed accounts: {len(self.cleanup_report['removed_accounts'])}",
            f"  Preserved accounts: {len(self.cleanup_report['preserved_accounts'])}",
            ""
        ]
        
        if self.cleanup_report["backup_created"]:
            report_lines.extend([
                f"Backup created: {self.cleanup_report['backup_created']}",
                ""
            ])
        
        if self.cleanup_report["removed_accounts"]:
            report_lines.extend([
                "Removed Accounts:",
                "-" * 20
            ])
            for account in self.cleanup_report["removed_accounts"]:
                report_lines.append(f"  - {account['email']} ({account['full_name']}) - {account['reason']}")
            report_lines.append("")
        
        if self.cleanup_report["preserved_accounts"]:
            report_lines.extend([
                "Preserved Accounts:",
                "-" * 20
            ])
            for account in self.cleanup_report["preserved_accounts"]:
                report_lines.append(f"  - {account['email']} ({account['full_name']}) - {account['reason']}")
            report_lines.append("")
        
        if self.cleanup_report["validation_issues"]:
            report_lines.extend([
                "Validation Issues:",
                "-" * 20
            ])
            for issue in self.cleanup_report["validation_issues"]:
                report_lines.append(f"  - {issue}")
            report_lines.append("")
        
        return "\n".join(report_lines)