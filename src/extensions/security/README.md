# Extension Security Features

This module provides enterprise-grade security features for the Kari Extensions System, including code signing, audit logging, access control, and vulnerability scanning.

## Features

### 1. Extension Code Signing and Verification

Ensures extension integrity and authenticity through cryptographic signatures.

**Key Components:**
- `ExtensionCodeSigner`: Signs extensions with RSA private keys
- `ExtensionVerifier`: Verifies extension signatures
- `ExtensionSignatureManager`: Manages signatures in database

**Usage:**
```python
# Sign an extension
signer = ExtensionCodeSigner(private_key_path, key_id)
signature_hash = signer.sign_extension(
    extension_path=Path("extensions/my-extension"),
    extension_name="my-extension",
    extension_version="1.0.0",
    signer_id="developer@company.com"
)

# Verify an extension
verifier = ExtensionVerifier(Path("keys/public"))
is_valid, verification_data = verifier.verify_extension(
    Path("extensions/my-extension")
)
```

**CLI Usage:**
```bash
# Generate key pair
python -m src.core.extensions.security.cli signing generate-keys \
    --output-dir ./keys --key-id production

# Sign extension
python -m src.core.extensions.security.cli signing sign \
    --extension-path ./extensions/my-extension \
    --extension-name my-extension \
    --extension-version 1.0.0 \
    --private-key ./keys/production_private.pem \
    --signer-id developer@company.com

# Verify extension
python -m src.core.extensions.security.cli signing verify \
    --extension-path ./extensions/my-extension \
    --public-keys-dir ./keys
```

### 2. Audit Logging and Compliance Reporting

Comprehensive logging of all extension activities for compliance and security monitoring.

**Key Components:**
- `ExtensionAuditLogger`: Logs extension activities
- `ExtensionComplianceReporter`: Generates compliance reports

**Logged Events:**
- Extension installation/uninstallation
- Permission changes
- Data access operations
- API calls
- Security violations

**Usage:**
```python
# Log extension installation
audit_logger = ExtensionAuditLogger(db_session)
audit_logger.log_extension_install(
    extension_name="my-extension",
    extension_version="1.0.0",
    tenant_id="tenant-123",
    user_id="user-456",
    source="marketplace"
)

# Generate compliance report
compliance_reporter = ExtensionComplianceReporter(db_session, audit_logger)
report = compliance_reporter.generate_compliance_report(
    tenant_id="tenant-123",
    report_type="security",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)
```

**CLI Usage:**
```bash
# Export audit logs
python -m src.core.extensions.security.cli audit logs \
    --db-url postgresql://user:pass@localhost/db \
    --tenant-id tenant-123 \
    --days 30 \
    --output audit_logs.json

# Generate compliance report
python -m src.core.extensions.security.cli audit compliance-report \
    --db-url postgresql://user:pass@localhost/db \
    --tenant-id tenant-123 \
    --report-type security \
    --days 30 \
    --output compliance_report.json
```

### 3. Access Control Policies

Fine-grained access control for extension resources and operations.

**Key Components:**
- `ExtensionAccessControlManager`: Manages access policies
- `AccessPolicy`: Defines access rules
- `AccessPolicyRule`: Individual access rule

**Policy Structure:**
```python
policy = AccessPolicy(
    extension_name="my-extension",
    tenant_id="tenant-123",
    policy_name="user_data_access",
    rules=[
        AccessPolicyRule(
            resource="data/users/*",
            action="read",
            conditions={"user_roles": ["user", "admin"]},
            effect="allow"
        ),
        AccessPolicyRule(
            resource="data/users/*",
            action="delete",
            conditions={"user_roles": ["admin"]},
            effect="allow"
        )
    ]
)
```

**Usage:**
```python
# Create access policy
access_manager = ExtensionAccessControlManager(db_session)
created_policy = access_manager.create_policy(policy, "admin-user")

# Check access
allowed = access_manager.check_access(
    extension_name="my-extension",
    tenant_id="tenant-123",
    user_id="user-456",
    resource="data/users/profile",
    action="read"
)

# Enforce access (raises exception if denied)
access_manager.enforce_access(
    extension_name="my-extension",
    tenant_id="tenant-123",
    user_id="user-456",
    resource="data/users/profile",
    action="delete"
)
```

### 4. Vulnerability Scanning

Automated security scanning for code vulnerabilities, dependency issues, and permission problems.

**Key Components:**
- `ExtensionVulnerabilityScanner`: Performs security scans
- `SecurityScanRequest`: Scan configuration
- `VulnerabilityFinding`: Individual vulnerability

**Scan Types:**
- **Code Analysis**: Detects dangerous patterns (code injection, SQL injection, etc.)
- **Dependency Analysis**: Checks for vulnerable package versions
- **Permission Analysis**: Reviews extension permissions
- **Deep Scan**: Additional security checks

**Usage:**
```python
# Perform vulnerability scan
scanner = ExtensionVulnerabilityScanner(db_session)
scan_request = SecurityScanRequest(
    extension_name="my-extension",
    extension_version="1.0.0",
    scan_types=["code", "dependencies", "permissions"],
    deep_scan=True
)

result = scanner.scan_extension(
    extension_path=Path("extensions/my-extension"),
    extension_name="my-extension",
    extension_version="1.0.0",
    scan_request=scan_request
)

print(f"Security Score: {result.security_score}")
print(f"Vulnerabilities: {len(result.vulnerabilities)}")
```

**CLI Usage:**
```bash
# Scan extension
python -m src.core.extensions.security.cli scan vulnerability \
    --extension-path ./extensions/my-extension \
    --extension-name my-extension \
    --extension-version 1.0.0 \
    --scan-types code,dependencies,permissions \
    --deep-scan \
    --db-url postgresql://user:pass@localhost/db \
    --output scan_results.json
```

## API Endpoints

### Code Signing
- `POST /api/extensions/security/sign` - Sign an extension
- `POST /api/extensions/security/verify` - Verify extension signature
- `GET /api/extensions/security/signatures` - List signatures

### Audit Logging
- `GET /api/extensions/security/audit/logs` - Get audit logs
- `GET /api/extensions/security/audit/summary` - Get audit summary
- `POST /api/extensions/security/audit/cleanup` - Clean up old logs

### Compliance Reporting
- `POST /api/extensions/security/compliance/report` - Generate compliance report

### Access Control
- `POST /api/extensions/security/access/policies` - Create access policy
- `GET /api/extensions/security/access/policies` - List access policies
- `GET /api/extensions/security/access/policies/{id}` - Get specific policy
- `PUT /api/extensions/security/access/policies/{id}` - Update policy
- `DELETE /api/extensions/security/access/policies/{id}` - Delete policy
- `POST /api/extensions/security/access/check` - Check access permissions

### Vulnerability Scanning
- `POST /api/extensions/security/vulnerabilities/scan` - Scan extension
- `GET /api/extensions/security/vulnerabilities` - Get vulnerabilities
- `PUT /api/extensions/security/vulnerabilities/{id}/status` - Update vulnerability status

### Security Dashboard
- `GET /api/extensions/security/dashboard/overview` - Get security overview

## Configuration

Configure security features through environment variables:

```bash
# Code signing
EXTENSION_SECURITY_SIGNING_ENABLED=true
EXTENSION_SECURITY_PRIVATE_KEY_PATH=/path/to/private.pem
EXTENSION_SECURITY_PUBLIC_KEYS_DIR=/path/to/public/keys
EXTENSION_SECURITY_SIGNATURE_REQUIRED=false

# Audit logging
EXTENSION_SECURITY_AUDIT_ENABLED=true
EXTENSION_SECURITY_AUDIT_RETENTION_DAYS=90
EXTENSION_SECURITY_HIGH_RISK_THRESHOLD=5

# Access control
EXTENSION_SECURITY_ACCESS_CONTROL_ENABLED=true
EXTENSION_SECURITY_DEFAULT_DENY=true
EXTENSION_SECURITY_POLICY_CACHE_TTL=300

# Vulnerability scanning
EXTENSION_SECURITY_VULNERABILITY_SCANNING_ENABLED=true
EXTENSION_SECURITY_SCAN_ON_INSTALL=true
EXTENSION_SECURITY_MAX_CRITICAL_VULNERABILITIES=0
EXTENSION_SECURITY_MAX_HIGH_VULNERABILITIES=5
EXTENSION_SECURITY_MIN_SECURITY_SCORE=70.0

# Notifications
EXTENSION_SECURITY_WEBHOOK_URL=https://hooks.example.com/security
EXTENSION_SECURITY_SLACK_WEBHOOK_URL=https://hooks.slack.com/...
EXTENSION_SECURITY_EMAIL_NOTIFICATIONS=false
```

## Database Schema

The security system uses the following database tables:

- `extension_signatures` - Extension code signatures
- `extension_audit_logs` - Audit log entries
- `extension_access_policies` - Access control policies
- `extension_vulnerabilities` - Vulnerability findings

Run the migration to create tables:

```sql
-- Run the migration script
\i src/core/extensions/security/migrations/001_create_security_tables.sql
```

Or use the CLI:

```bash
python -m src.core.extensions.security.cli init-db \
    --db-url postgresql://user:pass@localhost/db
```

## Integration with Extension System

The security features integrate seamlessly with the extension system:

```python
# During extension installation
security_service = ExtensionSecurityService(db_session)

security_report = await security_service.secure_extension_installation(
    extension_path=extension_path,
    extension_name=extension_name,
    extension_version=extension_version,
    tenant_id=tenant_id,
    user_id=user_id
)

if not security_report['allowed']:
    raise ExtensionSecurityError("Extension failed security checks")

# During runtime operations
await security_service.enforce_runtime_security(
    extension_name=extension_name,
    tenant_id=tenant_id,
    user_id=user_id,
    resource="data/users",
    action="read"
)
```

## Security Best Practices

1. **Code Signing**
   - Use separate keys for development and production
   - Store private keys securely (HSM, key vault)
   - Rotate keys regularly
   - Require signatures for production extensions

2. **Audit Logging**
   - Enable comprehensive logging
   - Monitor high-risk events
   - Set up automated alerts
   - Regular log analysis and retention

3. **Access Control**
   - Follow principle of least privilege
   - Regular policy reviews
   - Use role-based access control
   - Monitor policy violations

4. **Vulnerability Scanning**
   - Scan all extensions before installation
   - Regular periodic scans
   - Automated dependency updates
   - Immediate response to critical vulnerabilities

5. **Compliance**
   - Regular compliance reports
   - Document security procedures
   - Staff security training
   - Incident response procedures

## Troubleshooting

### Common Issues

1. **Signature Verification Fails**
   - Check public key is available
   - Verify key ID matches
   - Ensure extension hasn't been modified

2. **Access Denied Errors**
   - Check access policies are configured
   - Verify user roles and permissions
   - Review audit logs for details

3. **High Vulnerability Count**
   - Update dependencies to latest versions
   - Review and fix code issues
   - Consider security code review

4. **Performance Issues**
   - Optimize database queries
   - Implement caching for policies
   - Tune scan frequency

### Monitoring and Alerts

Set up monitoring for:
- Critical vulnerabilities detected
- High-risk security events
- Policy violations
- Failed signature verifications
- Low compliance scores

## Development and Testing

Run tests:
```bash
pytest src/core/extensions/security/test_security.py -v
```

The test suite covers:
- Code signing and verification
- Audit logging functionality
- Access control policies
- Vulnerability scanning
- Integration scenarios

## Support and Documentation

For additional support:
- Review API documentation
- Check configuration examples
- Run CLI help commands
- Review audit logs for troubleshooting