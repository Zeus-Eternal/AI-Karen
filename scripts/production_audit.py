#!/usr/bin/env python3
"""
Production Readiness Audit CLI

Command-line interface for running production readiness audits on the codebase.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.services.production_hardening_audit import (
    create_production_audit_service,
    ProductionHardeningAuditService
)


async def run_audit(directories: list, output_dir: str, formats: list, verbose: bool):
    """Run the production readiness audit."""
    print("🔍 Starting Production Readiness Audit...")
    print(f"📁 Scanning directories: {', '.join(directories)}")
    print(f"📊 Output directory: {output_dir}")
    print()
    
    # Create audit service
    service = create_production_audit_service(
        scan_directories=directories,
        output_directory=output_dir
    )
    
    try:
        # Initialize and start service
        await service.startup()
        
        # Run audit
        report = await service.audit_codebase()
        
        # Print summary
        print("📋 AUDIT SUMMARY")
        print("=" * 50)
        print(f"Files Scanned: {report.total_files_scanned}")
        print(f"Issues Found: {report.total_issues_found}")
        print(f"Scan Duration: {report.scan_duration_seconds:.2f}s")
        print(f"Overall Status: {report.overall_status}")
        print()
        
        # Print issues by severity
        if report.issues_by_severity:
            print("Issues by Severity:")
            for severity, count in report.issues_by_severity.items():
                emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️", "info": "📝"}.get(severity.value, "•")
                print(f"  {emoji} {severity.value.title()}: {count}")
            print()
        
        # Print issues by type
        if report.issues_by_type:
            print("Issues by Type:")
            for issue_type, count in report.issues_by_type.items():
                print(f"  • {issue_type.value.replace('_', ' ').title()}: {count}")
            print()
        
        # Print recommendations
        if report.recommendations:
            print("🎯 RECOMMENDATIONS")
            print("=" * 50)
            for rec in report.recommendations:
                print(f"  {rec}")
            print()
        
        # Generate reports in requested formats
        report_files = []
        for format_type in formats:
            try:
                report_file = await service.generate_report(report, format_type)
                report_files.append(report_file)
                print(f"📄 {format_type.upper()} report saved: {report_file}")
            except Exception as e:
                print(f"❌ Failed to generate {format_type} report: {e}")
        
        # Print detailed issues if verbose
        if verbose and report.issues:
            print("\n🔍 DETAILED ISSUES")
            print("=" * 50)
            for i, issue in enumerate(report.issues[:20], 1):  # Limit to first 20 for readability
                severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(issue.severity.value, "•")
                print(f"\n{i}. {severity_emoji} {issue.issue_type.value.replace('_', ' ').title()}")
                print(f"   File: {issue.file_path}:{issue.line_number}")
                print(f"   Description: {issue.description}")
                print(f"   Code: {issue.code_snippet}")
                print(f"   Fix: {issue.recommendation}")
            
            if len(report.issues) > 20:
                print(f"\n... and {len(report.issues) - 20} more issues. See full report for details.")
        
        # Shutdown service
        await service.shutdown()
        
        # Exit with appropriate code
        if report.issues_by_severity.get("critical", 0) > 0:
            print("\n❌ CRITICAL ISSUES FOUND - Production deployment blocked!")
            return 2
        elif report.issues_by_severity.get("high", 0) > 10:
            print("\n⚠️  TOO MANY HIGH-SEVERITY ISSUES - Review required!")
            return 1
        elif report.total_issues_found > 0:
            print("\n⚡ Issues found - Review recommended before production deployment")
            return 0
        else:
            print("\n✅ No issues found - Codebase appears production-ready!")
            return 0
            
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 3


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run production readiness audit on the codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/production_audit.py                    # Audit default directories
  python scripts/production_audit.py --dirs src ui_launchers  # Audit specific directories
  python scripts/production_audit.py --format html markdown   # Generate HTML and Markdown reports
  python scripts/production_audit.py --verbose               # Show detailed issues
  python scripts/production_audit.py --output /tmp/audit     # Custom output directory
        """
    )
    
    parser.add_argument(
        "--dirs", "--directories",
        nargs="+",
        default=["src", "ui_launchers", "extensions", "config"],
        help="Directories to scan (default: src ui_launchers extensions config)"
    )
    
    parser.add_argument(
        "--output", "--output-dir",
        default="reports/production_audit",
        help="Output directory for reports (default: reports/production_audit)"
    )
    
    parser.add_argument(
        "--format", "--formats",
        nargs="+",
        choices=["json", "html", "markdown"],
        default=["json"],
        help="Report formats to generate (default: json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed issues in console output"
    )
    
    args = parser.parse_args()
    
    # Run the audit
    try:
        exit_code = asyncio.run(run_audit(
            directories=args.dirs,
            output_dir=args.output,
            formats=args.format,
            verbose=args.verbose
        ))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()