# Extension Security Guide

## Overview

Security is paramount in the Kari Extension System. This guide covers security best practices for both extension developers and users, ensuring a safe and secure extension ecosystem.

## Security Architecture

### Isolation and Sandboxing

Extensions run in isolated environments with the following security measures:

**Process Isolation**
- Each extension runs in a separate process
- Memory isolation prevents cross-extension access
- Process limits prevent resource exhaustion
- Automatic cleanup on extension termination

**Permission System**
- Granular permission model
- Principle of least privilege
- Runtime permission validation
- Permission audit logging

**Resource Limits**
- CPU usage limits per extension
- Memory allocation constraints
- Disk space quotas
- Network bandwidth throttling

**Data Isolation**
- Tenant-specific data storage
- Encrypted data at rest
- Secure data transmission
- Automatic data cleanup

## Permission Model

### Permission Categories

**Data Permissions**
```json
{
  "data.read": "Read extension-specific data",
  "data.write": "Write extension-specific data", 
  "data.delete": "Delete extension-specific data",
  "data.user.read": "Read user profile data",
  "data.user.write": "Modify user profile data",
  "data.system.read": "Read system configuration",
  "data.global.read": "Read cross-tenant data"
}
```

**API Permissions**
```json
{
  "api.create_endpoints": "Create HTTP endpoints",
  "api.access_system": "Access system APIs",
  "api.external_requests": "Make external HTTP requests",
  "api.webhook.create": "Create webhook endpoints",
  "api.webhook.receive": "Receive webhook data"
}
```

**UI Permissions**
```json
{
  "ui.register_components": "Register UI components",
  "ui.register_pages": "Create full pages",
  "ui.modify_navigation": "Modify navigation menu",
  "ui.access_admin": "Access admin interface",
  "ui.inject_scripts": "Inject JavaScript code"
}
```

**System Permissions**
```json
{
  "system.background_tasks": "Run background tasks",
  "system.event_handlers": "Handle system events",
  "system.file_access": "Access file system",
  "system.process_spawn": "Spawn child processes",
  "system.network_raw": "Raw network access"
}
```

### Permission Validation

Extensions must declare required permissions in their manifest:

```json
{
  "name": "my-extension",
  "permissions": [
    "data.read",
    "data.write",
    "api.external_requests"
  ],
  "optional_permissions": [
    "ui.register_components"
  ]
}
```

Runtime permission checking:

```python
from kari.extensions.security import require_permission

class MyExtension(BaseExtension):
    @require_permission("data.write")
    async def save_data(self, data):
        await self.data_manager.create(data)
    
    async def conditional_operation(self):
        if self.has_permission("ui.register_components"):
            # Register UI component
            pass
        else:
            # Fallback behavior
            pass
```

## Secure Development Practices

### Input Validation

Always validate and sanitize user inputs:

```python
from kari.extensions.validation import validate_input
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    name: str
    email: str
    age: int
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError('Name must be 2-50 characters')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        # Use proper email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v.lower()

class MyExtension(BaseExtension):
    @endpoint("/api/my-extension/user", methods=["POST"])
    async def create_user(self, request):
        try:
            data = await request.json()
            user_input = UserInput(**data)
            # Process validated data
            return {"status": "success"}
        except ValueError as e:
            raise HTTPException(400, str(e))
```

### SQL Injection Prevention

Use parameterized queries and ORM methods:

```python
# ❌ Vulnerable to SQL injection
async def get_user_bad(self, user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return await self.data_manager.raw_query(query)

# ✅ Safe parameterized query
async def get_user_good(self, user_id):
    return await self.data_manager.get(user_id)

# ✅ Safe filtered query
async def search_users_good(self, name):
    return await self.data_manager.query({"name": {"$regex": name}})
```

### XSS Prevention

Sanitize output data for web display:

```python
import html
from markupsafe import escape

class MyExtension(BaseExtension):
    @endpoint("/api/my-extension/content", methods=["GET"])
    async def get_content(self, request):
        content = await self.data_manager.get("content")
        
        # Escape HTML content
        safe_content = {
            "title": escape(content["title"]),
            "body": escape(content["body"]),
            "html": html.escape(content["html"])
        }
        
        return safe_content
```

### Authentication and Authorization

Implement proper authentication checks:

```python
from kari.extensions.auth import get_current_user, require_role

class MyExtension(BaseExtension):
    @endpoint("/api/my-extension/profile", methods=["GET"])
    @require_auth
    async def get_profile(self, request):
        user = get_current_user(request)
        profile = await self.data_manager.query({
            "user_id": user.id
        })
        return {"profile": profile}
    
    @endpoint("/api/my-extension/admin", methods=["POST"])
    @require_role(["admin", "moderator"])
    async def admin_action(self, request):
        # Only admins and moderators can access
        pass
```

### Secure Configuration

Handle sensitive configuration securely:

```python
import os
from kari.extensions.crypto import encrypt_value, decrypt_value

class MyExtension(BaseExtension):
    async def initialize(self):
        # Get API key from secure configuration
        self.api_key = self.config.get_secret("api_key")
        
        # Encrypt sensitive data before storage
        sensitive_data = "user-secret-data"
        encrypted = encrypt_value(sensitive_data, self.encryption_key)
        await self.data_manager.set("encrypted_data", encrypted)
    
    async def get_sensitive_data(self):
        encrypted = await self.data_manager.get("encrypted_data")
        return decrypt_value(encrypted, self.encryption_key)
```

### Error Handling

Implement secure error handling:

```python
import logging
from kari.extensions.errors import ExtensionError

class MyExtension(BaseExtension):
    async def risky_operation(self, user_input):
        try:
            # Perform operation
            result = await self.external_api_call(user_input)
            return result
        except ExternalAPIError as e:
            # Log detailed error for debugging
            self.logger.error(f"External API error: {e}", extra={
                "user_id": self.current_user.id,
                "input_hash": hash(str(user_input))
            })
            
            # Return generic error to user
            raise ExtensionError(
                "Service temporarily unavailable",
                code="SERVICE_ERROR"
            )
        except Exception as e:
            # Log unexpected errors
            self.logger.exception("Unexpected error in risky_operation")
            
            # Don't expose internal details
            raise ExtensionError(
                "An unexpected error occurred",
                code="INTERNAL_ERROR"
            )
```

## Security Testing

### Static Analysis

Use security linting tools:

```bash
# Install security tools
pip install bandit safety semgrep

# Run security analysis
bandit -r my_extension/
safety check
semgrep --config=auto my_extension/
```

### Dependency Scanning

Regularly scan dependencies for vulnerabilities:

```bash
# Check for known vulnerabilities
pip-audit

# Update dependencies
pip-review --auto

# Use dependency pinning
pip freeze > requirements.txt
```

### Penetration Testing

Test extension security:

```python
# tests/test_security.py
import pytest
from kari.testing import ExtensionTestClient

class TestSecurity:
    async def test_sql_injection(self):
        client = ExtensionTestClient()
        
        # Test SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin'/**/OR/**/1=1#"
        ]
        
        for input_val in malicious_inputs:
            response = await client.get(f"/api/my-extension/search?q={input_val}")
            assert response.status_code != 500  # Should not crash
            # Verify no unauthorized data access
    
    async def test_xss_prevention(self):
        client = ExtensionTestClient()
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            response = await client.post("/api/my-extension/content", json={
                "content": payload
            })
            
            # Verify content is escaped
            assert "<script>" not in response.text
            assert "javascript:" not in response.text
    
    async def test_authorization(self):
        client = ExtensionTestClient()
        
        # Test unauthorized access
        response = await client.get("/api/my-extension/admin")
        assert response.status_code == 401
        
        # Test with regular user
        await client.login("regular_user")
        response = await client.get("/api/my-extension/admin")
        assert response.status_code == 403
        
        # Test with admin user
        await client.login("admin_user")
        response = await client.get("/api/my-extension/admin")
        assert response.status_code == 200
```

## Deployment Security

### Code Signing

Sign extension packages for integrity verification:

```bash
# Generate signing key
kari extension generate-key --name my-extension

# Sign extension package
kari extension sign my-extension-1.0.0.tar.gz --key my-extension.key

# Verify signature
kari extension verify my-extension-1.0.0.tar.gz --key my-extension.pub
```

### Secure Distribution

Use secure channels for extension distribution:

- **HTTPS Only**: All downloads over encrypted connections
- **Checksum Verification**: SHA-256 checksums for all packages
- **Digital Signatures**: Cryptographic signatures for authenticity
- **Malware Scanning**: Automated security scanning
- **Vulnerability Database**: Track and patch security issues

### Environment Security

Secure the deployment environment:

```yaml
# docker-compose.yml
version: '3.8'
services:
  kari-extension:
    image: kari/extension-runtime:latest
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    user: "1000:1000"
    environment:
      - KARI_SECURITY_MODE=strict
      - KARI_EXTENSION_ISOLATION=true
```

## Monitoring and Incident Response

### Security Monitoring

Monitor extension security events:

```python
from kari.extensions.monitoring import SecurityMonitor

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__()
        self.security_monitor = SecurityMonitor(self)
    
    async def sensitive_operation(self, user_id, action):
        # Log security-relevant events
        self.security_monitor.log_event(
            event_type="sensitive_operation",
            user_id=user_id,
            action=action,
            ip_address=self.request.client.host,
            user_agent=self.request.headers.get("user-agent")
        )
        
        # Check for suspicious patterns
        if self.security_monitor.is_suspicious_activity(user_id):
            self.security_monitor.alert(
                "Suspicious activity detected",
                severity="high",
                user_id=user_id
            )
```

### Audit Logging

Implement comprehensive audit logging:

```python
from kari.extensions.audit import AuditLogger

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__()
        self.audit = AuditLogger(self)
    
    async def create_record(self, data):
        record_id = await self.data_manager.create(data)
        
        # Log the creation
        await self.audit.log(
            action="record.create",
            resource_type="user_record",
            resource_id=record_id,
            user_id=self.current_user.id,
            details={"fields_modified": list(data.keys())}
        )
        
        return record_id
    
    async def delete_record(self, record_id):
        # Get record before deletion for audit
        record = await self.data_manager.get(record_id)
        
        await self.data_manager.delete(record_id)
        
        # Log the deletion
        await self.audit.log(
            action="record.delete",
            resource_type="user_record",
            resource_id=record_id,
            user_id=self.current_user.id,
            details={"deleted_data": record}
        )
```

### Incident Response

Prepare for security incidents:

```python
from kari.extensions.security import IncidentResponse

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__()
        self.incident_response = IncidentResponse(self)
    
    async def handle_security_incident(self, incident_type, details):
        # Immediate response
        if incident_type == "data_breach":
            # Disable extension immediately
            await self.disable_extension()
            
            # Notify security team
            await self.incident_response.notify_security_team(
                incident_type=incident_type,
                severity="critical",
                details=details
            )
            
            # Lock down affected resources
            await self.incident_response.lockdown_resources(
                affected_users=details.get("affected_users", [])
            )
        
        elif incident_type == "suspicious_activity":
            # Rate limit the user
            await self.incident_response.rate_limit_user(
                user_id=details["user_id"],
                duration=3600  # 1 hour
            )
            
            # Require re-authentication
            await self.incident_response.require_reauth(
                user_id=details["user_id"]
            )
```

## Compliance and Regulations

### GDPR Compliance

Implement GDPR requirements:

```python
from kari.extensions.gdpr import GDPRCompliance

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__()
        self.gdpr = GDPRCompliance(self)
    
    async def handle_data_request(self, request_type, user_id):
        if request_type == "export":
            # Export all user data
            user_data = await self.data_manager.query({
                "user_id": user_id
            })
            return await self.gdpr.export_user_data(user_data)
        
        elif request_type == "delete":
            # Delete all user data
            await self.data_manager.delete_where({
                "user_id": user_id
            })
            await self.gdpr.log_deletion(user_id)
        
        elif request_type == "rectification":
            # Allow user to correct their data
            return await self.gdpr.get_rectification_form(user_id)
```

### SOC 2 Compliance

Implement SOC 2 controls:

```python
from kari.extensions.compliance import SOC2Controls

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__()
        self.soc2 = SOC2Controls(self)
    
    async def initialize(self):
        # Implement access controls
        await self.soc2.setup_access_controls()
        
        # Enable audit logging
        await self.soc2.enable_audit_logging()
        
        # Configure data encryption
        await self.soc2.configure_encryption()
        
        # Set up monitoring
        await self.soc2.setup_monitoring()
```

## Security Checklist

### Development Phase

- [ ] Input validation implemented
- [ ] Output sanitization in place
- [ ] Authentication and authorization checks
- [ ] Secure configuration management
- [ ] Error handling doesn't leak information
- [ ] Dependencies scanned for vulnerabilities
- [ ] Static security analysis passed
- [ ] Security tests written and passing

### Pre-Deployment

- [ ] Code review completed
- [ ] Security testing performed
- [ ] Penetration testing conducted
- [ ] Documentation reviewed
- [ ] Incident response plan prepared
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures tested

### Post-Deployment

- [ ] Security monitoring active
- [ ] Audit logging enabled
- [ ] Regular security scans scheduled
- [ ] Vulnerability management process
- [ ] Incident response procedures tested
- [ ] Security training for users
- [ ] Regular security reviews scheduled

## Security Resources

### Tools and Libraries

**Static Analysis**
- Bandit: Python security linter
- Semgrep: Multi-language static analysis
- CodeQL: Semantic code analysis
- SonarQube: Code quality and security

**Dependency Scanning**
- Safety: Python dependency scanner
- Snyk: Multi-language vulnerability scanner
- OWASP Dependency Check: Open source scanner
- GitHub Security Advisories: Automated alerts

**Runtime Security**
- Falco: Runtime security monitoring
- Sysdig: Container security platform
- Twistlock: Container security
- Aqua Security: Cloud native security

### Security Standards

- **OWASP Top 10**: Web application security risks
- **NIST Cybersecurity Framework**: Security guidelines
- **ISO 27001**: Information security management
- **SOC 2**: Security and availability controls
- **GDPR**: Data protection regulation

### Training and Certification

- **OWASP WebGoat**: Hands-on security training
- **Certified Ethical Hacker (CEH)**: Ethical hacking certification
- **CISSP**: Information security certification
- **Security+**: CompTIA security certification
- **GSEC**: SANS security essentials

## Reporting Security Issues

### Responsible Disclosure

If you discover a security vulnerability:

1. **Do Not** disclose publicly immediately
2. **Email** security@kari.ai with details
3. **Include** steps to reproduce the issue
4. **Provide** your contact information
5. **Wait** for acknowledgment and guidance

### Bug Bounty Program

Kari operates a bug bounty program for security researchers:

- **Scope**: All Kari extensions and infrastructure
- **Rewards**: $100 - $10,000 based on severity
- **Requirements**: Responsible disclosure
- **Timeline**: 90 days for fix before public disclosure

### Security Advisory Process

1. **Report Received**: Security team acknowledges within 24 hours
2. **Triage**: Issue severity and impact assessment
3. **Investigation**: Detailed analysis and reproduction
4. **Fix Development**: Patch development and testing
5. **Disclosure**: Coordinated public disclosure
6. **Recognition**: Credit to security researcher

---

*Security is everyone's responsibility. By following these guidelines, we can maintain a secure and trustworthy extension ecosystem.*