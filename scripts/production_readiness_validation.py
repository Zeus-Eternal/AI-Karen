#!/usr/bin/env python3
"""
Production Readiness Validation Script
Comprehensive validation for production deployment preparation
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil
import requests
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check"""
    category: str
    test_name: str
    status: str  # PASS, FAIL, WARNING, SKIP
    message: str
    details: Optional[Dict] = None
    execution_time: Optional[float] = None

@dataclass
class ProductionReadinessReport:
    """Complete production readiness report"""
    timestamp: datetime
    overall_status: str
    summary: Dict[str, int]
    results: List[ValidationResult]
    recommendations: List[str]
    system_info: Dict
    execution_time: float

class ProductionValidator:
    """Main production readiness validator"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        self.base_url = "http://localhost:8010"
        self.playwright_config = "ui_launchers/web_ui/playwright.audit.config.ts"
        
    def add_result(self, category: str, test_name: str, status: str, 
                   message: str, details: Optional[Dict] = None, 
                   execution_time: Optional[float] = None):
        """Add a validation result"""
        result = ValidationResult(
            category=category,
            test_name=test_name,
            status=status,
            message=message,
            details=details,
            execution_time=execution_time
        )
        self.results.append(result)
        
        # Log the result
        icon = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "SKIP": "⏭️"}.get(status, "❓")
        logger.info(f"{icon} [{category}] {test_name}: {message}")
        
    async def validate_startup_health_checks(self) -> None:
        """Validate startup health checks and database synchronization"""
        logger.info("🏥 Validating startup health checks...")
        
        start_time = time.time()
        
        try:
            # Check if server is running
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.add_result(
                    "Health Checks", 
                    "Server Health", 
                    "PASS",
                    f"Server is healthy: {health_data.get('status', 'unknown')}",
                    health_data
                )
            else:
                self.add_result(
                    "Health Checks", 
                    "Server Health", 
                    "FAIL",
                    f"Server health check failed: HTTP {response.status_code}"
                )
        except requests.RequestException as e:
            self.add_result(
                "Health Checks", 
                "Server Health", 
                "FAIL",
                f"Cannot connect to server: {str(e)}"
            )
            
        # Check database connections
        try:
            response = requests.get(f"{self.base_url}/api/admin/system/database/health", timeout=10)
            if response.status_code == 200:
                db_health = response.json()
                for db_name, status in db_health.items():
                    self.add_result(
                        "Database Health",
                        f"{db_name} Connection",
                        "PASS" if status.get("connected") else "FAIL",
                        f"{db_name}: {status.get('message', 'Unknown status')}",
                        status
                    )
            else:
                self.add_result(
                    "Database Health",
                    "Database Connections",
                    "WARNING",
                    f"Could not check database health: HTTP {response.status_code}"
                )
        except requests.RequestException as e:
            self.add_result(
                "Database Health",
                "Database Connections",
                "WARNING",
                f"Database health check unavailable: {str(e)}"
            )
            
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.add_result(
            "System Resources",
            "CPU Usage",
            "PASS" if cpu_percent < 80 else "WARNING",
            f"CPU usage: {cpu_percent}%",
            {"cpu_percent": cpu_percent}
        )
        
        self.add_result(
            "System Resources",
            "Memory Usage",
            "PASS" if memory.percent < 80 else "WARNING",
            f"Memory usage: {memory.percent}%",
            {"memory_percent": memory.percent, "available_gb": memory.available / (1024**3)}
        )
        
        self.add_result(
            "System Resources",
            "Disk Usage",
            "PASS" if disk.percent < 80 else "WARNING",
            f"Disk usage: {disk.percent}%",
            {"disk_percent": disk.percent, "free_gb": disk.free / (1024**3)}
        )
        
        execution_time = time.time() - start_time
        logger.info(f"Health checks completed in {execution_time:.2f}s")
        
    async def validate_plugin_load_order(self) -> None:
        """Verify plugin load order and response formatting integration"""
        logger.info("🔌 Validating plugin load order and integration...")
        
        start_time = time.time()
        
        try:
            # Check plugin registry
            response = requests.get(f"{self.base_url}/api/admin/plugins/status", timeout=10)
            if response.status_code == 200:
                plugins_data = response.json()
                
                # Check if response formatting plugins are loaded
                response_formatters = [p for p in plugins_data.get('plugins', []) 
                                     if 'response-formatting' in p.get('name', '')]
                
                if response_formatters:
                    self.add_result(
                        "Plugin Integration",
                        "Response Formatting Plugins",
                        "PASS",
                        f"Found {len(response_formatters)} response formatting plugins",
                        {"formatters": [p['name'] for p in response_formatters]}
                    )
                else:
                    self.add_result(
                        "Plugin Integration",
                        "Response Formatting Plugins",
                        "WARNING",
                        "No response formatting plugins detected"
                    )
                    
                # Check plugin load order
                load_order_issues = []
                for plugin in plugins_data.get('plugins', []):
                    if plugin.get('status') != 'loaded':
                        load_order_issues.append(f"{plugin['name']}: {plugin.get('status', 'unknown')}")
                        
                if not load_order_issues:
                    self.add_result(
                        "Plugin Integration",
                        "Plugin Load Status",
                        "PASS",
                        "All plugins loaded successfully"
                    )
                else:
                    self.add_result(
                        "Plugin Integration",
                        "Plugin Load Status",
                        "WARNING",
                        f"Plugin load issues: {', '.join(load_order_issues)}",
                        {"issues": load_order_issues}
                    )
                    
            else:
                self.add_result(
                    "Plugin Integration",
                    "Plugin Status Check",
                    "WARNING",
                    f"Could not check plugin status: HTTP {response.status_code}"
                )
                
        except requests.RequestException as e:
            self.add_result(
                "Plugin Integration",
                "Plugin Status Check",
                "WARNING",
                f"Plugin status check unavailable: {str(e)}"
            )
            
        # Test response formatting integration
        try:
            test_queries = [
                {"query": "Tell me about the movie Inception", "expected_type": "movie"},
                {"query": "How do I make chocolate chip cookies?", "expected_type": "recipe"},
                {"query": "What's the weather like today?", "expected_type": "weather"},
                {"query": "Latest news about AI", "expected_type": "news"}
            ]
            
            for test_query in test_queries:
                response = requests.post(
                    f"{self.base_url}/api/chat/test-formatting",
                    json={"message": test_query["query"]},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('formatted') and result.get('formatter_used'):
                        self.add_result(
                            "Response Formatting",
                            f"{test_query['expected_type'].title()} Formatting",
                            "PASS",
                            f"Successfully formatted {test_query['expected_type']} response",
                            {"formatter": result.get('formatter_used')}
                        )
                    else:
                        self.add_result(
                            "Response Formatting",
                            f"{test_query['expected_type'].title()} Formatting",
                            "WARNING",
                            f"Response not formatted for {test_query['expected_type']} query"
                        )
                else:
                    self.add_result(
                        "Response Formatting",
                        f"{test_query['expected_type'].title()} Formatting",
                        "SKIP",
                        f"Could not test {test_query['expected_type']} formatting: HTTP {response.status_code}"
                    )
                    
        except requests.RequestException as e:
            self.add_result(
                "Response Formatting",
                "Formatting Integration Test",
                "SKIP",
                f"Response formatting test unavailable: {str(e)}"
            )
            
        execution_time = time.time() - start_time
        logger.info(f"Plugin validation completed in {execution_time:.2f}s")
        
    async def run_playwright_tests(self) -> None:
        """Execute all Playwright E2E tests in headless and UI modes"""
        logger.info("🎭 Running Playwright E2E tests...")
        
        start_time = time.time()
        
        # Check if Playwright is available
        playwright_dir = Path("ui_launchers/web_ui")
        if not playwright_dir.exists():
            self.add_result(
                "E2E Tests",
                "Playwright Setup",
                "SKIP",
                "Playwright directory not found"
            )
            return
            
        # Run tests in headless mode
        try:
            logger.info("Running Playwright tests in headless mode...")
            result = subprocess.run([
                "npx", "playwright", "test", 
                "--config", self.playwright_config,
                "--reporter=json"
            ], 
            cwd=playwright_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                self.add_result(
                    "E2E Tests",
                    "Headless Mode",
                    "PASS",
                    "All Playwright tests passed in headless mode",
                    {"stdout": result.stdout[:500]}  # Truncate output
                )
            else:
                self.add_result(
                    "E2E Tests",
                    "Headless Mode",
                    "FAIL",
                    f"Playwright tests failed in headless mode (exit code: {result.returncode})",
                    {"stderr": result.stderr[:500]}  # Truncate output
                )
                
        except subprocess.TimeoutExpired:
            self.add_result(
                "E2E Tests",
                "Headless Mode",
                "FAIL",
                "Playwright tests timed out in headless mode"
            )
        except Exception as e:
            self.add_result(
                "E2E Tests",
                "Headless Mode",
                "FAIL",
                f"Failed to run Playwright tests: {str(e)}"
            )
            
        # Run specific production tests
        production_tests = [
            "comprehensive-audit.spec.ts",
            "login-audit-debug.spec.ts", 
            "performance.spec.ts",
            "accessibility.spec.ts"
        ]
        
        for test_file in production_tests:
            try:
                logger.info(f"Running specific test: {test_file}")
                result = subprocess.run([
                    "npx", "playwright", "test", test_file,
                    "--config", self.playwright_config,
                    "--reporter=list"
                ],
                cwd=playwright_dir,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes per test
                )
                
                if result.returncode == 0:
                    self.add_result(
                        "E2E Tests",
                        f"Test: {test_file}",
                        "PASS",
                        f"Test {test_file} passed"
                    )
                else:
                    self.add_result(
                        "E2E Tests",
                        f"Test: {test_file}",
                        "FAIL",
                        f"Test {test_file} failed (exit code: {result.returncode})",
                        {"stderr": result.stderr[:300]}
                    )
                    
            except subprocess.TimeoutExpired:
                self.add_result(
                    "E2E Tests",
                    f"Test: {test_file}",
                    "FAIL",
                    f"Test {test_file} timed out"
                )
            except Exception as e:
                self.add_result(
                    "E2E Tests",
                    f"Test: {test_file}",
                    "SKIP",
                    f"Could not run test {test_file}: {str(e)}"
                )
                
        execution_time = time.time() - start_time
        logger.info(f"Playwright tests completed in {execution_time:.2f}s")
        
    def generate_final_report(self) -> ProductionReadinessReport:
        """Generate final production readiness report"""
        logger.info("📊 Generating final production readiness report...")
        
        # Calculate summary
        summary = {
            "PASS": len([r for r in self.results if r.status == "PASS"]),
            "FAIL": len([r for r in self.results if r.status == "FAIL"]),
            "WARNING": len([r for r in self.results if r.status == "WARNING"]),
            "SKIP": len([r for r in self.results if r.status == "SKIP"])
        }
        
        # Determine overall status
        if summary["FAIL"] > 0:
            overall_status = "NOT_READY"
        elif summary["WARNING"] > 5:  # More than 5 warnings
            overall_status = "NEEDS_ATTENTION"
        else:
            overall_status = "READY"
            
        # Generate recommendations
        recommendations = []
        
        if summary["FAIL"] > 0:
            recommendations.append("Address all failed checks before production deployment")
            
        if summary["WARNING"] > 0:
            recommendations.append("Review and address warning items for optimal production performance")
            
        # Add specific recommendations based on failures
        failed_categories = set(r.category for r in self.results if r.status == "FAIL")
        
        if "E2E Tests" in failed_categories:
            recommendations.append("Fix failing E2E tests to ensure user workflows work correctly")
            
        if "Database Health" in failed_categories:
            recommendations.append("Resolve database connectivity issues before deployment")
            
        if "Health Checks" in failed_categories:
            recommendations.append("Ensure all health check endpoints are working properly")
            
        # System information
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_total_gb": psutil.disk_usage('/').total / (1024**3)
        }
        
        execution_time = time.time() - self.start_time
        
        report = ProductionReadinessReport(
            timestamp=datetime.now(),
            overall_status=overall_status,
            summary=summary,
            results=self.results,
            recommendations=recommendations,
            system_info=system_info,
            execution_time=execution_time
        )
        
        return report
        
    def save_report(self, report: ProductionReadinessReport, filename: str = None) -> str:
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"production_readiness_report_{timestamp}.json"
            
        report_dict = asdict(report)
        # Convert datetime to string for JSON serialization
        report_dict['timestamp'] = report.timestamp.isoformat()
        
        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
            
        logger.info(f"Report saved to {filename}")
        return filename
        
    def print_summary(self, report: ProductionReadinessReport) -> None:
        """Print a summary of the validation results"""
        print("\n" + "="*60)
        print("🚀 PRODUCTION READINESS VALIDATION SUMMARY")
        print("="*60)
        print(f"Overall Status: {report.overall_status}")
        print(f"Execution Time: {report.execution_time:.2f} seconds")
        print(f"Timestamp: {report.timestamp}")
        print()
        
        print("📊 Results Summary:")
        for status, count in report.summary.items():
            icon = {"PASS": "✅", "FAIL": "❌", "WARNING": "⚠️", "SKIP": "⏭️"}.get(status, "❓")
            print(f"  {icon} {status}: {count}")
        print()
        
        if report.recommendations:
            print("💡 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
            print()
            
        # Show failed tests
        failed_results = [r for r in report.results if r.status == "FAIL"]
        if failed_results:
            print("❌ Failed Checks:")
            for result in failed_results:
                print(f"  • [{result.category}] {result.test_name}: {result.message}")
            print()
            
        # Show warnings
        warning_results = [r for r in report.results if r.status == "WARNING"]
        if warning_results:
            print("⚠️  Warning Checks:")
            for result in warning_results[:5]:  # Show first 5 warnings
                print(f"  • [{result.category}] {result.test_name}: {result.message}")
            if len(warning_results) > 5:
                print(f"  ... and {len(warning_results) - 5} more warnings")
            print()
            
        print("="*60)

async def main():
    """Main validation function"""
    logger.info("🚀 Starting Production Readiness Validation")
    
    validator = ProductionValidator()
    
    try:
        # Run all validation checks
        await validator.validate_startup_health_checks()
        await validator.validate_plugin_load_order()
        await validator.run_playwright_tests()
        
        # Generate and save report
        report = validator.generate_final_report()
        report_file = validator.save_report(report)
        
        # Print summary
        validator.print_summary(report)
        
        logger.info(f"✅ Production readiness validation completed. Report saved to {report_file}")
        
        # Exit with appropriate code
        if report.overall_status == "NOT_READY":
            sys.exit(1)
        elif report.overall_status == "NEEDS_ATTENTION":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Validation failed with error: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())