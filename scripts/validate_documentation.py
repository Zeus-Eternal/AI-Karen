#!/usr/bin/env python3
"""
Documentation Validation Orchestrator

This script runs all documentation validation utilities in sequence
and provides a comprehensive report.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse


class DocumentationValidationOrchestrator:
    """Orchestrates all documentation validation tools"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.scripts_path = self.root_path / "scripts"
        
    def run_system_analysis(self) -> bool:
        """Run system analysis to extract current codebase information"""
        print("🔍 Running system analysis...")
        
        script_path = self.scripts_path / "doc_analysis.py"
        if not script_path.exists():
            print(f"❌ System analysis script not found: {script_path}")
            return False
        
        try:
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=self.root_path)
            
            if result.returncode == 0:
                print("✅ System analysis completed successfully")
                return True
            else:
                print(f"❌ System analysis failed:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error running system analysis: {e}")
            return False
    
    def run_documentation_validation(self) -> bool:
        """Run documentation validation against implementation"""
        print("\n📋 Running documentation validation...")
        
        script_path = self.scripts_path / "doc_validation.py"
        if not script_path.exists():
            print(f"❌ Documentation validation script not found: {script_path}")
            return False
        
        try:
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=self.root_path)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            return result.returncode == 0
                
        except Exception as e:
            print(f"❌ Error running documentation validation: {e}")
            return False
    
    def run_link_checking(self, external_only: bool = False, internal_only: bool = False) -> bool:
        """Run automated link checking"""
        print("\n🔗 Running link checking...")
        
        script_path = self.scripts_path / "link_checker.py"
        if not script_path.exists():
            print(f"❌ Link checker script not found: {script_path}")
            return False
        
        try:
            cmd = [sys.executable, str(script_path)]
            if external_only:
                cmd.append("--external-only")
            elif internal_only:
                cmd.append("--internal-only")
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_path)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            return result.returncode == 0
                
        except Exception as e:
            print(f"❌ Error running link checking: {e}")
            return False
    
    def run_code_example_validation(self) -> bool:
        """Run code example validation"""
        print("\n💻 Running code example validation...")
        
        script_path = self.scripts_path / "code_example_validator.py"
        if not script_path.exists():
            print(f"❌ Code example validator script not found: {script_path}")
            return False
        
        try:
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, cwd=self.root_path)
            
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            
            return result.returncode == 0
                
        except Exception as e:
            print(f"❌ Error running code example validation: {e}")
            return False
    
    def generate_summary_report(self, results: Dict[str, bool]) -> None:
        """Generate a summary report of all validation results"""
        print("\n" + "="*60)
        print("📊 DOCUMENTATION VALIDATION SUMMARY")
        print("="*60)
        
        total_checks = len(results)
        passed_checks = sum(1 for success in results.values() if success)
        failed_checks = total_checks - passed_checks
        
        for check_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{check_name:<30} {status}")
        
        print("-" * 60)
        print(f"Total checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {failed_checks}")
        
        if failed_checks == 0:
            print("\n🎉 All documentation validation checks passed!")
            print("Your documentation is consistent with the implementation.")
        else:
            print(f"\n⚠️  {failed_checks} validation check(s) failed.")
            print("Please review the output above and fix the issues.")
        
        # Save summary to file
        summary_file = self.root_path / "documentation_validation_summary.json"
        summary_data = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "results": results,
            "overall_status": "passed" if failed_checks == 0 else "failed"
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"\n📄 Detailed summary saved to: {summary_file}")
    
    def run_all_validations(self, skip_analysis: bool = False, skip_links: bool = False, 
                          skip_code: bool = False, external_only: bool = False, 
                          internal_only: bool = False) -> bool:
        """Run all documentation validation checks"""
        print("🚀 Starting comprehensive documentation validation...")
        print(f"Working directory: {self.root_path}")
        
        results = {}
        
        # Step 1: System Analysis (unless skipped)
        if not skip_analysis:
            results["System Analysis"] = self.run_system_analysis()
        else:
            print("⏭️  Skipping system analysis")
            results["System Analysis"] = True
        
        # Step 2: Documentation Validation
        results["Documentation Validation"] = self.run_documentation_validation()
        
        # Step 3: Link Checking (unless skipped)
        if not skip_links:
            results["Link Checking"] = self.run_link_checking(external_only, internal_only)
        else:
            print("⏭️  Skipping link checking")
            results["Link Checking"] = True
        
        # Step 4: Code Example Validation (unless skipped)
        if not skip_code:
            results["Code Example Validation"] = self.run_code_example_validation()
        else:
            print("⏭️  Skipping code example validation")
            results["Code Example Validation"] = True
        
        # Generate summary report
        self.generate_summary_report(results)
        
        # Return overall success
        return all(results.values())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Comprehensive documentation validation suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_documentation.py                    # Run all validations
  python validate_documentation.py --skip-analysis    # Skip system analysis
  python validate_documentation.py --skip-links       # Skip link checking
  python validate_documentation.py --external-only    # Check only external links
  python validate_documentation.py --internal-only    # Check only internal links
        """
    )
    
    parser.add_argument("--skip-analysis", action="store_true", 
                       help="Skip system analysis (use existing system_analysis.json)")
    parser.add_argument("--skip-links", action="store_true", 
                       help="Skip link checking")
    parser.add_argument("--skip-code", action="store_true", 
                       help="Skip code example validation")
    parser.add_argument("--external-only", action="store_true", 
                       help="Check only external links")
    parser.add_argument("--internal-only", action="store_true", 
                       help="Check only internal links")
    parser.add_argument("--root", default=".", 
                       help="Root directory of the project (default: current directory)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.external_only and args.internal_only:
        print("❌ Cannot specify both --external-only and --internal-only")
        sys.exit(1)
    
    # Create orchestrator and run validations
    orchestrator = DocumentationValidationOrchestrator(args.root)
    
    success = orchestrator.run_all_validations(
        skip_analysis=args.skip_analysis,
        skip_links=args.skip_links,
        skip_code=args.skip_code,
        external_only=args.external_only,
        internal_only=args.internal_only
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()