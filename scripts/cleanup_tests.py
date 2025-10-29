#!/usr/bin/env python3
"""
Cleanup script for AI-Karen test reorganization
Removes temporary files, scripts, and documentation created during the test organization process.
"""

import os
import shutil
from pathlib import Path


def cleanup_temp_files():
    """Remove temporary files and documentation."""
    base_path = Path("/media/zeus/Development10/KIRO/AI-Karen")
    
    # Temporary files to remove
    temp_files = [
        "merge_tests.py",
        "TEST_MERGE_COMPLETE.md", 
        "TEST_ORGANIZATION_COMPLETE.md",
    ]
    
    removed_files = []
    
    for temp_file in temp_files:
        file_path = base_path / temp_file
        if file_path.exists():
            file_path.unlink()
            removed_files.append(temp_file)
            print(f"🗑️  Removed: {temp_file}")
    
    return removed_files


def cleanup_old_backups():
    """Remove old .env backups (keep the most recent one)."""
    base_path = Path("/media/zeus/Development10/KIRO/AI-Karen")
    
    # Find all .env backup files
    env_backups = list(base_path.glob(".env.backup.*"))
    
    if len(env_backups) > 1:
        # Sort by modification time, keep the newest
        env_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove all but the most recent
        for backup in env_backups[1:]:
            backup.unlink()
            print(f"🗑️  Removed old backup: {backup.name}")
        
        print(f"✅ Kept most recent backup: {env_backups[0].name}")
    
    return len(env_backups) - 1 if len(env_backups) > 1 else 0


def ask_about_test_backup():
    """Ask user if they want to remove the test backup."""
    backup_path = Path("/media/zeus/Development10/KIRO/AI-Karen/tests_backup_20250921_175525")
    
    if backup_path.exists():
        print(f"\n📦 Found test backup: {backup_path.name}")
        print("This contains the original unorganized test structure.")
        
        response = input("Remove this backup? (y/N): ")
        if response.lower() == 'y':
            shutil.rmtree(backup_path)
            print(f"🗑️  Removed: {backup_path.name}")
            return True
        else:
            print(f"✅ Keeping backup: {backup_path.name}")
            return False
    
    return False


def cleanup_empty_dirs():
    """Remove any empty directories that might be left."""
    base_path = Path("/media/zeus/Development10/KIRO/AI-Karen")
    
    # Check for empty temp_files directory
    temp_files_dir = base_path / "temp_files"
    if temp_files_dir.exists() and not any(temp_files_dir.iterdir()):
        temp_files_dir.rmdir()
        print(f"🗑️  Removed empty directory: temp_files")
        return True
    
    return False


def main():
    """Main cleanup function."""
    print("🧹 AI-Karen Test Organization Cleanup")
    print("=" * 40)
    
    # Remove temporary files
    removed_files = cleanup_temp_files()
    
    # Cleanup old backups
    removed_backups = cleanup_old_backups()
    
    # Ask about test backup
    removed_test_backup = ask_about_test_backup()
    
    # Remove empty directories
    removed_empty_dirs = cleanup_empty_dirs()
    
    # Summary
    print("\n" + "=" * 40)
    print("✅ Cleanup Summary:")
    print(f"   Temporary files removed: {len(removed_files)}")
    print(f"   Old backups removed: {removed_backups}")
    print(f"   Test backup removed: {'Yes' if removed_test_backup else 'No'}")
    print(f"   Empty directories removed: {'Yes' if removed_empty_dirs else 'No'}")
    
    if removed_files:
        print(f"\n📁 Files removed: {', '.join(removed_files)}")
    
    print("\n🎉 Your AI-Karen project is now clean and organized!")
    print("The test structure is ready for development:")
    print("   - tests/ directory with organized structure")
    print("   - run_tests.py for convenient test execution")
    print("   - pytest.ini with proper configuration")
    print("   - Complete documentation in tests/README.md")


if __name__ == "__main__":
    main()
