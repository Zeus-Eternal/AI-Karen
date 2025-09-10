#!/usr/bin/env python3
"""
System initialization script for AI Karen Engine.
Run this script to ensure all necessary files, folders, models, and dependencies are set up.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ai_karen_engine.core.initialization import SystemInitializer


async def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(
        description="Initialize AI Karen Engine system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/initialize_system.py                    # Initialize system
  python scripts/initialize_system.py --force           # Force reinstall all components
  python scripts/initialize_system.py --models-only     # Only setup models
  python scripts/initialize_system.py --check-health    # Check system health
        """
    )
    
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force reinstallation of all components"
    )
    
    parser.add_argument(
        "--models-only",
        action="store_true", 
        help="Only setup models and skip other components"
    )
    
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Check system health without making changes"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    initializer = SystemInitializer()
    
    print("🚀 AI Karen Engine System Initialization")
    print("=" * 50)
    
    if args.check_health:
        print("🔍 Checking system health...")
        health_ok = await initializer._validate_system_health()
        if health_ok:
            print("✅ System health check passed!")
            return 0
        else:
            print("❌ System health check failed!")
            return 1
    
    if args.models_only:
        print("📥 Setting up models only...")
        success = await initializer._setup_models(args.force)
        if success:
            print("✅ Models setup completed!")
            return 0
        else:
            print("❌ Models setup failed!")
            return 1
    
    # Full system initialization
    print("🔧 Initializing complete system...")
    results = await initializer.initialize_system(args.force)
    
    # Print results
    print("\n📊 Initialization Results:")
    print("-" * 30)
    
    for component, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {component.title()}: {'Success' if success else 'Failed'}")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"\n📈 Overall: {success_count}/{total_count} components successful")
    
    if success_count == total_count:
        print("\n🎉 System initialization completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Start the AI Karen Engine: python start.py")
        print("   2. Check the web interface at http://localhost:8000")
        print("   3. Review logs in the logs/ directory")
        return 0
    else:
        print("\n⚠️ System initialization completed with some issues.")
        print("   Check the logs above for details on failed components.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Initialization failed with error: {e}")
        sys.exit(1)