#!/usr/bin/env python3
"""
Comprehensive security testing automation script.
Runs penetration tests, compliance checks, and security audits.
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.security.penetration_testing import PenetrationTestSuite, SecurityScanner

# Import optional components with error handling
try:
    from ai_karen_engine.security.threat_protection import ThreatProtectionSystem
    THREAT_PROTECTION_AVAILABLE = True
except ImportError:
    ThreatProtectionSystem = None
    THREAT_PROTECTION_AVAILABLE = False

try:
    from ai_karen_engine.security.incident_response import SecurityIncidentManager
    INCIDENT_RESPONSE_AVAILABLE = True
except ImportError:
    SecurityIncidentManager = None
    INCIDENT_RESPONSE_AVAILABLE = False

try:
    from ai_karen_engine.security.compliance import ComplianceReporter
    COMPLIANCE_AVAILABLE = True
except ImportError:
    ComplianceReporter = None
    COMPLIANCE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SecurityTestRunner:
    """Orchestrates comprehensive security testing."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        
    async def run_penetration_tests(self, endpoints: List[str]) -> Dict[str, Any]:
        """Run comprehensive penetration tests."""
        logger.info("Starting penetration testing suite")
        
        pen_test_suite = PenetrationTestSuite(self.base_url)
        
        try:
            result = await pen_test_suite.run_comprehensive_test(endpoints)
            
            # Generate executive summary
            executive_summary = pen_test_suite.generate_executive_summary(result)
            
            pen_test_results = {
                'test_id': result.test_id,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'tests_run': result.tests_run,
                'tests_passed': result.tests_passed,
                'tests_failed': result.tests_failed,
                'coverage_percentage': result.coverage_percentage,
                'risk_score': result.risk_score,
                'vulnerabilities_found': len(result.vulnerabilities),
                'executive_summary': executive_summary,
                'vulnerabilities': [
                    {
                        'id': vuln.id,
                        'title': vuln.title,
                        'severity': vuln.severity.value,
                        'category': vuln.category.value,
                        'description': vuln.description,
                        'affected_endpoint': vuln.affected_endpoint,
                        'remediation': vuln.remediation
                    }
                    for vuln in result.vulnerabilities
                ]
            }
            
            self.results['penetration_testing'] = pen_test_results
            logger.info(f"Penetration testing completed. Found {len(result.vulnerabilities)} vulnerabilities")
            
            return pen_test_results
            
        except Exception as e:
            logger.error(f"Error running penetration tests: {e}")
            return {'error': str(e)}
    
    async def run_compliance_audit(self) -> Dict[str, Any]:
        """Run compliance audits for SOC2, GDPR, etc."""
        logger.info("Starting compliance audit")
        
        try:
            # Mock Redis and database for testing
            import aioredis
            from unittest.mock import AsyncMock
            
            redis_client = AsyncMock()
            database_session = AsyncMock()
            
            # Configure mock responses for testing
            redis_client.get.return_value = "true"
            redis_client.keys.return_value = []
            redis_client.exists.return_value = True
            redis_client.hgetall.return_value = {}
            redis_client.hset = AsyncMock()
            redis_client.expire = AsyncMock()
            redis_client.setex = AsyncMock()
            
            compliance_reporter = ComplianceReporter(redis_client, database_session)
            
            # Generate compliance reports
            reports = await compliance_reporter.generate_comprehensive_report()
            
            compliance_results = {}
            for framework, report in reports.items():
                compliance_results[framework] = {
                    'report_id': report.id,
                    'framework': report.framework.value,
                    'report_date': report.report_date.isoformat(),
                    'overall_status': report.overall_status.value,
                    'controls_assessed': report.controls_assessed,
                    'controls_compliant': report.controls_compliant,
                    'controls_non_compliant': report.controls_non_compliant,
                    'risk_score': report.risk_score,
                    'findings_count': len(report.findings),
                    'recommendations_count': len(report.recommendations)
                }
            
            self.results['compliance_audit'] = compliance_results
            logger.info(f"Compliance audit completed for {len(reports)} frameworks")
            
            return compliance_results
            
        except Exception as e:
            logger.error(f"Error running compliance audit: {e}")
            return {'error': str(e)}
    
    async def run_security_scan(self, endpoints: List[str]) -> Dict[str, Any]:
        """Run automated security scanning."""
        logger.info("Starting security scanning")
        
        try:
            async with SecurityScanner(self.base_url) as scanner:
                all_vulnerabilities = []
                
                # SQL Injection scan
                sql_vulns = await scanner.scan_sql_injection(endpoints)
                all_vulnerabilities.extend(sql_vulns)
                
                # XSS scan
                xss_vulns = await scanner.scan_xss(endpoints)
                all_vulnerabilities.extend(xss_vulns)
                
                # Authentication bypass scan
                auth_vulns = await scanner.scan_authentication_bypass(endpoints)
                all_vulnerabilities.extend(auth_vulns)
                
                # API security scan
                api_vulns = await scanner.scan_api_security(endpoints)
                all_vulnerabilities.extend(api_vulns)
                
                scan_results = {
                    'scan_date': datetime.utcnow().isoformat(),
                    'endpoints_scanned': len(endpoints),
                    'vulnerabilities_found': len(all_vulnerabilities),
                    'vulnerability_breakdown': {
                        'sql_injection': len(sql_vulns),
                        'xss': len(xss_vulns),
                        'auth_bypass': len(auth_vulns),
                        'api_security': len(api_vulns)
                    },
                    'vulnerabilities': [
                        {
                            'id': vuln.id,
                            'title': vuln.title,
                            'severity': vuln.severity.value,
                            'category': vuln.category.value,
                            'endpoint': vuln.affected_endpoint,
                            'description': vuln.description
                        }
                        for vuln in all_vulnerabilities
                    ]
                }
                
                self.results['security_scan'] = scan_results
                logger.info(f"Security scan completed. Found {len(all_vulnerabilities)} vulnerabilities")
                
                return scan_results
                
        except Exception as e:
            logger.error(f"Error running security scan: {e}")
            return {'error': str(e)}
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        report = {
            'report_generated': datetime.utcnow().isoformat(),
            'summary': {
                'total_tests_run': 0,
                'total_vulnerabilities': 0,
                'critical_vulnerabilities': 0,
                'high_vulnerabilities': 0,
                'compliance_status': 'unknown'
            },
            'results': self.results,
            'recommendations': []
        }
        
        # Calculate summary statistics
        if 'penetration_testing' in self.results:
            pen_test = self.results['penetration_testing']
            report['summary']['total_tests_run'] += pen_test.get('tests_run', 0)
            
            for vuln in pen_test.get('vulnerabilities', []):
                if vuln['severity'] == 'critical':
                    report['summary']['critical_vulnerabilities'] += 1
                elif vuln['severity'] == 'high':
                    report['summary']['high_vulnerabilities'] += 1
        
        if 'security_scan' in self.results:
            scan = self.results['security_scan']
            report['summary']['total_vulnerabilities'] += scan.get('vulnerabilities_found', 0)
        
        # Generate recommendations
        recommendations = []
        
        if report['summary']['critical_vulnerabilities'] > 0:
            recommendations.append("URGENT: Address all critical vulnerabilities immediately")
            recommendations.append("Implement emergency security patches")
            recommendations.append("Consider taking affected systems offline until patched")
        
        if report['summary']['high_vulnerabilities'] > 0:
            recommendations.append("Prioritize fixing high-severity vulnerabilities")
            recommendations.append("Implement additional monitoring for affected endpoints")
        
        if 'compliance_audit' in self.results:
            for framework, compliance in self.results['compliance_audit'].items():
                if compliance.get('overall_status') == 'non_compliant':
                    recommendations.append(f"Address {framework.upper()} compliance issues immediately")
        
        recommendations.extend([
            "Implement automated security testing in CI/CD pipeline",
            "Conduct regular penetration testing",
            "Establish security monitoring and alerting",
            "Provide security training for development team",
            "Implement security code review process"
        ])
        
        report['recommendations'] = recommendations
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save security report to file."""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"security_report_{timestamp}.json"
        
        reports_dir = Path("security_reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / filename
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Security report saved to {report_file}")
        return report_file


async def main():
    """Main security testing function."""
    parser = argparse.ArgumentParser(description="Run comprehensive security testing")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for testing")
    parser.add_argument("--endpoints-file", 
                       help="JSON file containing endpoints to test")
    parser.add_argument("--skip-pentest", action="store_true",
                       help="Skip penetration testing")
    parser.add_argument("--skip-compliance", action="store_true",
                       help="Skip compliance audit")
    parser.add_argument("--skip-scan", action="store_true",
                       help="Skip security scan")
    parser.add_argument("--output", 
                       help="Output filename for report")
    
    args = parser.parse_args()
    
    # Load endpoints
    if args.endpoints_file:
        with open(args.endpoints_file, 'r') as f:
            endpoints_data = json.load(f)
            endpoints = endpoints_data.get('endpoints', [])
    else:
        # Default endpoints for AI Karen
        endpoints = [
            "/api/v1/chat",
            "/api/v1/users",
            "/api/v1/tenants",
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/memory",
            "/api/v1/plugins",
            "/api/v1/health",
            "/api/v1/metrics"
        ]
    
    logger.info(f"Starting security testing for {len(endpoints)} endpoints")
    
    # Initialize test runner
    test_runner = SecurityTestRunner(args.base_url)
    
    # Run tests
    if not args.skip_pentest:
        await test_runner.run_penetration_tests(endpoints)
    
    if not args.skip_compliance:
        await test_runner.run_compliance_audit()
    
    if not args.skip_scan:
        await test_runner.run_security_scan(endpoints)
    
    # Generate and save report
    report = test_runner.generate_security_report()
    report_file = test_runner.save_report(report, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("SECURITY TESTING SUMMARY")
    print("="*60)
    print(f"Report saved to: {report_file}")
    print(f"Total tests run: {report['summary']['total_tests_run']}")
    print(f"Total vulnerabilities: {report['summary']['total_vulnerabilities']}")
    print(f"Critical vulnerabilities: {report['summary']['critical_vulnerabilities']}")
    print(f"High vulnerabilities: {report['summary']['high_vulnerabilities']}")
    
    if report['summary']['critical_vulnerabilities'] > 0:
        print("\n⚠️  CRITICAL VULNERABILITIES FOUND - IMMEDIATE ACTION REQUIRED!")
    elif report['summary']['high_vulnerabilities'] > 0:
        print("\n⚠️  High-severity vulnerabilities found - prioritize fixes")
    else:
        print("\n✅ No critical or high-severity vulnerabilities found")
    
    print("\nTop Recommendations:")
    for i, rec in enumerate(report['recommendations'][:5], 1):
        print(f"{i}. {rec}")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())