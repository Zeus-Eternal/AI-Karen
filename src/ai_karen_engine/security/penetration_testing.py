"""
Comprehensive penetration testing and security scanning framework.
Provides automated security testing capabilities for the AI Karen platform.
"""

import asyncio
import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class VulnerabilityLevel(Enum):
    """Security vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestCategory(Enum):
    """Categories of security tests."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    SESSION_MANAGEMENT = "session_management"
    ENCRYPTION = "encryption"
    API_SECURITY = "api_security"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class SecurityVulnerability:
    """Represents a discovered security vulnerability."""
    id: str
    title: str
    description: str
    severity: VulnerabilityLevel
    category: TestCategory
    affected_endpoint: Optional[str] = None
    proof_of_concept: Optional[str] = None
    remediation: Optional[str] = None
    cve_references: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    tenant_id: Optional[str] = None


@dataclass
class PenetrationTestResult:
    """Results from a penetration test run."""
    test_id: str
    start_time: datetime
    end_time: datetime
    vulnerabilities: List[SecurityVulnerability]
    tests_run: int
    tests_passed: int
    tests_failed: int
    coverage_percentage: float
    risk_score: float


class SecurityScanner:
    """Automated security scanner for various attack vectors."""
    
    def __init__(self, base_url: str, session: Optional[aiohttp.ClientSession] = None):
        self.base_url = base_url.rstrip('/')
        self.session = session
        self.vulnerabilities: List[SecurityVulnerability] = []
        
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scan_sql_injection(self, endpoints: List[str]) -> List[SecurityVulnerability]:
        """Test for SQL injection vulnerabilities."""
        vulnerabilities = []
        
        # Common SQL injection payloads
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
            "admin'--",
            "' OR 1=1#",
            "1' OR '1'='1' /*",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for endpoint in endpoints:
            for payload in payloads:
                try:
                    # Test GET parameters
                    test_url = f"{self.base_url}{endpoint}?id={payload}"
                    async with self.session.get(test_url) as response:
                        content = await response.text()
                        
                        if self._detect_sql_error(content):
                            vulnerability = SecurityVulnerability(
                                id=f"sqli_{endpoint}_{hash(payload)}",
                                title="SQL Injection Vulnerability",
                                description=f"SQL injection detected in endpoint {endpoint}",
                                severity=VulnerabilityLevel.CRITICAL,
                                category=TestCategory.SQL_INJECTION,
                                affected_endpoint=endpoint,
                                proof_of_concept=f"Payload: {payload}",
                                remediation="Use parameterized queries and input validation"
                            )
                            vulnerabilities.append(vulnerability)
                    
                    # Test POST data
                    post_data = {"input": payload, "search": payload}
                    async with self.session.post(
                        f"{self.base_url}{endpoint}", 
                        json=post_data
                    ) as response:
                        content = await response.text()
                        
                        if self._detect_sql_error(content):
                            vulnerability = SecurityVulnerability(
                                id=f"sqli_post_{endpoint}_{hash(payload)}",
                                title="SQL Injection in POST Data",
                                description=f"SQL injection detected in POST data for {endpoint}",
                                severity=VulnerabilityLevel.CRITICAL,
                                category=TestCategory.SQL_INJECTION,
                                affected_endpoint=endpoint,
                                proof_of_concept=f"POST payload: {payload}",
                                remediation="Use parameterized queries and input validation"
                            )
                            vulnerabilities.append(vulnerability)
                            
                except Exception as e:
                    logger.warning(f"Error testing SQL injection on {endpoint}: {e}")
                    
        return vulnerabilities
    
    def _detect_sql_error(self, content: str) -> bool:
        """Detect SQL error messages in response content."""
        sql_errors = [
            "SQL syntax",
            "mysql_fetch",
            "ORA-[0-9]+",
            "PostgreSQL.*ERROR",
            "Warning.*mysql_",
            "valid MySQL result",
            "MySqlClient",
            "PostgreSQL query failed",
            "sqlite3.OperationalError",
            "SQLite/JDBCDriver",
            "SQLite.Exception",
            "System.Data.SQLite.SQLiteException",
            "Warning.*sqlite_",
            "Warning.*SQLite3::",
            "SQLITE_ERROR",
            "sqlite3.DatabaseError",
            "SQL error.*POS([0-9]+)",
            "Warning.*SQLite3 result index",
            "SyntaxError.*query",
            "MemSQL does not support this type of query",
            "is not supported by MemSQL",
            "unsupported nested scalar subselect"
        ]
        
        for error_pattern in sql_errors:
            if re.search(error_pattern, content, re.IGNORECASE):
                return True
        return False
    
    async def scan_xss(self, endpoints: List[str]) -> List[SecurityVulnerability]:
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        vulnerabilities = []
        
        # XSS payloads
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>"
        ]
        
        for endpoint in endpoints:
            for payload in payloads:
                try:
                    # Test reflected XSS
                    test_url = f"{self.base_url}{endpoint}?q={payload}"
                    async with self.session.get(test_url) as response:
                        content = await response.text()
                        
                        if payload in content and not self._is_payload_encoded(payload, content):
                            vulnerability = SecurityVulnerability(
                                id=f"xss_{endpoint}_{hash(payload)}",
                                title="Cross-Site Scripting (XSS) Vulnerability",
                                description=f"Reflected XSS detected in endpoint {endpoint}",
                                severity=VulnerabilityLevel.HIGH,
                                category=TestCategory.XSS,
                                affected_endpoint=endpoint,
                                proof_of_concept=f"Payload: {payload}",
                                remediation="Implement proper output encoding and CSP headers"
                            )
                            vulnerabilities.append(vulnerability)
                            
                except Exception as e:
                    logger.warning(f"Error testing XSS on {endpoint}: {e}")
                    
        return vulnerabilities
    
    def _is_payload_encoded(self, payload: str, content: str) -> bool:
        """Check if XSS payload is properly encoded in response."""
        encoded_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;'
        }
        
        for char, encoded in encoded_chars.items():
            if char in payload and encoded in content:
                return True
        return False
    
    async def scan_authentication_bypass(self, endpoints: List[str]) -> List[SecurityVulnerability]:
        """Test for authentication bypass vulnerabilities."""
        vulnerabilities = []
        
        bypass_techniques = [
            # Header manipulation
            {"headers": {"X-Forwarded-For": "127.0.0.1"}},
            {"headers": {"X-Real-IP": "127.0.0.1"}},
            {"headers": {"X-Originating-IP": "127.0.0.1"}},
            {"headers": {"X-Remote-IP": "127.0.0.1"}},
            {"headers": {"X-Client-IP": "127.0.0.1"}},
            
            # HTTP method manipulation
            {"method": "HEAD"},
            {"method": "OPTIONS"},
            {"method": "TRACE"},
            
            # Parameter pollution
            {"params": {"admin": "true"}},
            {"params": {"role": "admin"}},
            {"params": {"user_id": "1"}},
        ]
        
        for endpoint in endpoints:
            for technique in bypass_techniques:
                try:
                    method = technique.get("method", "GET")
                    headers = technique.get("headers", {})
                    params = technique.get("params", {})
                    
                    async with self.session.request(
                        method,
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        params=params
                    ) as response:
                        
                        # Check if bypass was successful (200 OK when should be 401/403)
                        if response.status == 200:
                            vulnerability = SecurityVulnerability(
                                id=f"auth_bypass_{endpoint}_{hash(str(technique))}",
                                title="Authentication Bypass",
                                description=f"Authentication bypass detected in {endpoint}",
                                severity=VulnerabilityLevel.CRITICAL,
                                category=TestCategory.AUTHENTICATION,
                                affected_endpoint=endpoint,
                                proof_of_concept=f"Technique: {technique}",
                                remediation="Implement proper authentication checks"
                            )
                            vulnerabilities.append(vulnerability)
                            
                except Exception as e:
                    logger.warning(f"Error testing auth bypass on {endpoint}: {e}")
                    
        return vulnerabilities
    
    async def scan_api_security(self, api_endpoints: List[str]) -> List[SecurityVulnerability]:
        """Test API-specific security vulnerabilities."""
        vulnerabilities = []
        
        for endpoint in api_endpoints:
            try:
                # Test for verbose error messages
                async with self.session.get(f"{self.base_url}{endpoint}/nonexistent") as response:
                    content = await response.text()
                    
                    if any(keyword in content.lower() for keyword in [
                        "traceback", "stack trace", "exception", "error:", "debug"
                    ]):
                        vulnerability = SecurityVulnerability(
                            id=f"verbose_errors_{endpoint}",
                            title="Verbose Error Messages",
                            description=f"API endpoint {endpoint} exposes verbose error messages",
                            severity=VulnerabilityLevel.MEDIUM,
                            category=TestCategory.API_SECURITY,
                            affected_endpoint=endpoint,
                            remediation="Implement generic error messages for production"
                        )
                        vulnerabilities.append(vulnerability)
                
                # Test for missing rate limiting
                start_time = time.time()
                requests_made = 0
                
                while time.time() - start_time < 5:  # Test for 5 seconds
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        requests_made += 1
                        if response.status == 429:  # Rate limited
                            break
                
                if requests_made > 100:  # More than 100 requests in 5 seconds
                    vulnerability = SecurityVulnerability(
                        id=f"no_rate_limit_{endpoint}",
                        title="Missing Rate Limiting",
                        description=f"API endpoint {endpoint} lacks rate limiting",
                        severity=VulnerabilityLevel.MEDIUM,
                        category=TestCategory.API_SECURITY,
                        affected_endpoint=endpoint,
                        remediation="Implement rate limiting middleware"
                    )
                    vulnerabilities.append(vulnerability)
                    
            except Exception as e:
                logger.warning(f"Error testing API security on {endpoint}: {e}")
                
        return vulnerabilities


class PenetrationTestSuite:
    """Comprehensive penetration testing suite."""
    
    def __init__(self, base_url: str, database_session: Optional[AsyncSession] = None):
        self.base_url = base_url
        self.database_session = database_session
        self.scanner = SecurityScanner(base_url)
        self.results: List[PenetrationTestResult] = []
        
    async def run_comprehensive_test(
        self, 
        endpoints: List[str],
        tenant_id: Optional[str] = None
    ) -> PenetrationTestResult:
        """Run comprehensive penetration testing suite."""
        test_id = f"pentest_{int(time.time())}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting comprehensive penetration test {test_id}")
        
        all_vulnerabilities = []
        tests_run = 0
        tests_passed = 0
        
        async with self.scanner:
            # SQL Injection Tests
            logger.info("Running SQL injection tests...")
            sql_vulns = await self.scanner.scan_sql_injection(endpoints)
            all_vulnerabilities.extend(sql_vulns)
            tests_run += len(endpoints) * 8  # 8 payloads per endpoint
            tests_passed += tests_run - len(sql_vulns)
            
            # XSS Tests
            logger.info("Running XSS tests...")
            xss_vulns = await self.scanner.scan_xss(endpoints)
            all_vulnerabilities.extend(xss_vulns)
            xss_tests = len(endpoints) * 10  # 10 payloads per endpoint
            tests_run += xss_tests
            tests_passed += xss_tests - len(xss_vulns)
            
            # Authentication Bypass Tests
            logger.info("Running authentication bypass tests...")
            auth_vulns = await self.scanner.scan_authentication_bypass(endpoints)
            all_vulnerabilities.extend(auth_vulns)
            auth_tests = len(endpoints) * 10  # 10 techniques per endpoint
            tests_run += auth_tests
            tests_passed += auth_tests - len(auth_vulns)
            
            # API Security Tests
            logger.info("Running API security tests...")
            api_vulns = await self.scanner.scan_api_security(endpoints)
            all_vulnerabilities.extend(api_vulns)
            api_tests = len(endpoints) * 2  # 2 tests per endpoint
            tests_run += api_tests
            tests_passed += api_tests - len(api_vulns)
        
        # Additional manual tests
        manual_vulns = await self._run_manual_tests(endpoints, tenant_id)
        all_vulnerabilities.extend(manual_vulns)
        
        end_time = datetime.utcnow()
        tests_failed = tests_run - tests_passed
        coverage_percentage = (tests_passed / tests_run * 100) if tests_run > 0 else 0
        risk_score = self._calculate_risk_score(all_vulnerabilities)
        
        result = PenetrationTestResult(
            test_id=test_id,
            start_time=start_time,
            end_time=end_time,
            vulnerabilities=all_vulnerabilities,
            tests_run=tests_run,
            tests_passed=tests_passed,
            tests_failed=tests_failed,
            coverage_percentage=coverage_percentage,
            risk_score=risk_score
        )
        
        self.results.append(result)
        await self._save_results(result, tenant_id)
        
        logger.info(f"Penetration test {test_id} completed. "
                   f"Found {len(all_vulnerabilities)} vulnerabilities. "
                   f"Risk score: {risk_score}")
        
        return result
    
    async def _run_manual_tests(
        self, 
        endpoints: List[str], 
        tenant_id: Optional[str]
    ) -> List[SecurityVulnerability]:
        """Run manual security tests that require custom logic."""
        vulnerabilities = []
        
        # Test for insecure direct object references
        if self.database_session:
            idor_vulns = await self._test_idor(endpoints, tenant_id)
            vulnerabilities.extend(idor_vulns)
        
        # Test for session management issues
        session_vulns = await self._test_session_management(endpoints)
        vulnerabilities.extend(session_vulns)
        
        # Test for CSRF vulnerabilities
        csrf_vulns = await self._test_csrf(endpoints)
        vulnerabilities.extend(csrf_vulns)
        
        return vulnerabilities
    
    async def _test_idor(
        self, 
        endpoints: List[str], 
        tenant_id: Optional[str]
    ) -> List[SecurityVulnerability]:
        """Test for Insecure Direct Object References."""
        vulnerabilities = []
        
        if not self.database_session or not tenant_id:
            return vulnerabilities
        
        try:
            # Get some object IDs from the database
            query = text(f"""
                SELECT id FROM tenant_{tenant_id}.conversations 
                LIMIT 5
            """)
            result = await self.database_session.execute(query)
            object_ids = [str(row[0]) for row in result.fetchall()]
            
            for endpoint in endpoints:
                if "{id}" in endpoint or "/id/" in endpoint:
                    for obj_id in object_ids:
                        test_endpoint = endpoint.replace("{id}", obj_id)
                        
                        # Test access with different tenant context
                        async with aiohttp.ClientSession() as session:
                            # Try to access with wrong tenant ID
                            headers = {"X-Tenant-ID": "different-tenant"}
                            async with session.get(
                                f"{self.base_url}{test_endpoint}",
                                headers=headers
                            ) as response:
                                
                                if response.status == 200:
                                    vulnerability = SecurityVulnerability(
                                        id=f"idor_{endpoint}_{obj_id}",
                                        title="Insecure Direct Object Reference",
                                        description=f"IDOR vulnerability in {endpoint}",
                                        severity=VulnerabilityLevel.HIGH,
                                        category=TestCategory.AUTHORIZATION,
                                        affected_endpoint=endpoint,
                                        proof_of_concept=f"Object ID {obj_id} accessible across tenants",
                                        remediation="Implement proper authorization checks"
                                    )
                                    vulnerabilities.append(vulnerability)
                                    
        except Exception as e:
            logger.warning(f"Error testing IDOR: {e}")
            
        return vulnerabilities
    
    async def _test_session_management(self, endpoints: List[str]) -> List[SecurityVulnerability]:
        """Test session management security."""
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            # Test for session fixation
            async with session.get(f"{self.base_url}/login") as response:
                initial_cookies = response.cookies
                
            # Simulate login
            login_data = {"username": "test", "password": "test"}
            async with session.post(f"{self.base_url}/login", json=login_data) as response:
                post_login_cookies = response.cookies
                
                # Check if session ID changed after login
                if initial_cookies.get('session_id') == post_login_cookies.get('session_id'):
                    vulnerability = SecurityVulnerability(
                        id="session_fixation",
                        title="Session Fixation Vulnerability",
                        description="Session ID does not change after authentication",
                        severity=VulnerabilityLevel.MEDIUM,
                        category=TestCategory.SESSION_MANAGEMENT,
                        affected_endpoint="/login",
                        remediation="Regenerate session ID after authentication"
                    )
                    vulnerabilities.append(vulnerability)
        
        return vulnerabilities
    
    async def _test_csrf(self, endpoints: List[str]) -> List[SecurityVulnerability]:
        """Test for CSRF vulnerabilities."""
        vulnerabilities = []
        
        post_endpoints = [ep for ep in endpoints if any(method in ep.lower() 
                                                       for method in ['post', 'put', 'delete'])]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in post_endpoints:
                try:
                    # Test POST without CSRF token
                    async with session.post(
                        f"{self.base_url}{endpoint}",
                        json={"test": "data"}
                    ) as response:
                        
                        # If request succeeds without CSRF protection
                        if response.status in [200, 201, 202]:
                            vulnerability = SecurityVulnerability(
                                id=f"csrf_{endpoint}",
                                title="Missing CSRF Protection",
                                description=f"Endpoint {endpoint} lacks CSRF protection",
                                severity=VulnerabilityLevel.MEDIUM,
                                category=TestCategory.CSRF,
                                affected_endpoint=endpoint,
                                remediation="Implement CSRF tokens for state-changing operations"
                            )
                            vulnerabilities.append(vulnerability)
                            
                except Exception as e:
                    logger.warning(f"Error testing CSRF on {endpoint}: {e}")
        
        return vulnerabilities
    
    def _calculate_risk_score(self, vulnerabilities: List[SecurityVulnerability]) -> float:
        """Calculate overall risk score based on vulnerabilities."""
        if not vulnerabilities:
            return 0.0
        
        severity_weights = {
            VulnerabilityLevel.CRITICAL: 10.0,
            VulnerabilityLevel.HIGH: 7.5,
            VulnerabilityLevel.MEDIUM: 5.0,
            VulnerabilityLevel.LOW: 2.5,
            VulnerabilityLevel.INFO: 1.0
        }
        
        total_score = sum(severity_weights.get(vuln.severity, 0) for vuln in vulnerabilities)
        max_possible_score = len(vulnerabilities) * 10.0
        
        return (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0.0
    
    async def _save_results(self, result: PenetrationTestResult, tenant_id: Optional[str]):
        """Save penetration test results to database and file."""
        # Save to file
        results_dir = Path("security_reports")
        results_dir.mkdir(exist_ok=True)
        
        report_file = results_dir / f"pentest_{result.test_id}.json"
        
        report_data = {
            "test_id": result.test_id,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat(),
            "tenant_id": tenant_id,
            "summary": {
                "tests_run": result.tests_run,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
                "coverage_percentage": result.coverage_percentage,
                "risk_score": result.risk_score,
                "vulnerabilities_found": len(result.vulnerabilities)
            },
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "title": vuln.title,
                    "description": vuln.description,
                    "severity": vuln.severity.value,
                    "category": vuln.category.value,
                    "affected_endpoint": vuln.affected_endpoint,
                    "proof_of_concept": vuln.proof_of_concept,
                    "remediation": vuln.remediation,
                    "discovered_at": vuln.discovered_at.isoformat()
                }
                for vuln in result.vulnerabilities
            ]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Penetration test report saved to {report_file}")
    
    def generate_executive_summary(self, result: PenetrationTestResult) -> str:
        """Generate executive summary of penetration test results."""
        critical_vulns = [v for v in result.vulnerabilities if v.severity == VulnerabilityLevel.CRITICAL]
        high_vulns = [v for v in result.vulnerabilities if v.severity == VulnerabilityLevel.HIGH]
        
        summary = f"""
PENETRATION TEST EXECUTIVE SUMMARY
==================================

Test ID: {result.test_id}
Test Duration: {result.end_time - result.start_time}
Risk Score: {result.risk_score:.1f}/100

VULNERABILITY SUMMARY:
- Critical: {len(critical_vulns)}
- High: {len(high_vulns)}
- Medium: {len([v for v in result.vulnerabilities if v.severity == VulnerabilityLevel.MEDIUM])}
- Low: {len([v for v in result.vulnerabilities if v.severity == VulnerabilityLevel.LOW])}
- Info: {len([v for v in result.vulnerabilities if v.severity == VulnerabilityLevel.INFO])}

IMMEDIATE ACTION REQUIRED:
"""
        
        if critical_vulns:
            summary += "\nCRITICAL VULNERABILITIES (Fix Immediately):\n"
            for vuln in critical_vulns[:5]:  # Top 5 critical
                summary += f"- {vuln.title} ({vuln.affected_endpoint})\n"
        
        if high_vulns:
            summary += "\nHIGH PRIORITY VULNERABILITIES:\n"
            for vuln in high_vulns[:5]:  # Top 5 high
                summary += f"- {vuln.title} ({vuln.affected_endpoint})\n"
        
        summary += f"""
TEST COVERAGE:
- Tests Run: {result.tests_run}
- Tests Passed: {result.tests_passed}
- Coverage: {result.coverage_percentage:.1f}%

RECOMMENDATIONS:
1. Address all critical vulnerabilities immediately
2. Implement security code review process
3. Add automated security testing to CI/CD pipeline
4. Conduct regular penetration testing
5. Implement security monitoring and alerting
"""
        
        return summary