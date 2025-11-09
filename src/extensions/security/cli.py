"""
CLI tools for extension security management
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .code_signing import ExtensionCodeSigner, ExtensionVerifier, ExtensionSignatureManager
from .audit_logger import ExtensionAuditLogger, ExtensionComplianceReporter
from .access_control import ExtensionAccessControlManager
from .vulnerability_scanner import ExtensionVulnerabilityScanner, SecurityScanRequest
from .models import Base


@click.group()
def security():
    """Extension security management commands"""
    pass


@security.group()
def signing():
    """Code signing commands"""
    pass


@signing.command()
@click.option('--extension-path', required=True, help='Path to extension directory')
@click.option('--extension-name', required=True, help='Extension name')
@click.option('--extension-version', required=True, help='Extension version')
@click.option('--private-key', required=True, help='Path to private key file')
@click.option('--key-id', default='default', help='Key identifier')
@click.option('--signer-id', required=True, help='Signer identifier')
def sign(extension_path: str, extension_name: str, extension_version: str, 
         private_key: str, key_id: str, signer_id: str):
    """Sign an extension"""
    try:
        signer = ExtensionCodeSigner(private_key, key_id)
        
        signature_hash = signer.sign_extension(
            extension_path=Path(extension_path),
            extension_name=extension_name,
            extension_version=extension_version,
            signer_id=signer_id
        )
        
        click.echo(f"Extension signed successfully. Signature hash: {signature_hash}")
        
    except Exception as e:
        click.echo(f"Error signing extension: {e}", err=True)
        sys.exit(1)


@signing.command()
@click.option('--extension-path', required=True, help='Path to extension directory')
@click.option('--public-keys-dir', required=True, help='Path to public keys directory')
def verify(extension_path: str, public_keys_dir: str):
    """Verify an extension signature"""
    try:
        verifier = ExtensionVerifier(Path(public_keys_dir))
        
        is_valid, verification_data = verifier.verify_extension(Path(extension_path))
        
        if is_valid:
            click.echo("✓ Extension signature is valid")
            click.echo(f"Signed by: {verification_data['signature_data']['signer_id']}")
            click.echo(f"Signed at: {verification_data['signature_data']['signed_at']}")
        else:
            click.echo("✗ Extension signature is invalid", err=True)
            if 'error' in verification_data:
                click.echo(f"Error: {verification_data['error']}", err=True)
            else:
                click.echo(f"Signature valid: {verification_data['signature_valid']}")
                click.echo(f"Hash valid: {verification_data['hash_valid']}")
        
        sys.exit(0 if is_valid else 1)
        
    except Exception as e:
        click.echo(f"Error verifying extension: {e}", err=True)
        sys.exit(1)


@signing.command()
@click.option('--output-dir', required=True, help='Output directory for keys')
@click.option('--key-id', required=True, help='Key identifier')
def generate_keys(output_dir: str, key_id: str):
    """Generate a new key pair for signing"""
    try:
        signer = ExtensionCodeSigner()
        
        private_key_path, public_key_path = signer.generate_key_pair(
            output_dir=Path(output_dir),
            key_id=key_id
        )
        
        click.echo(f"Key pair generated successfully:")
        click.echo(f"Private key: {private_key_path}")
        click.echo(f"Public key: {public_key_path}")
        
    except Exception as e:
        click.echo(f"Error generating keys: {e}", err=True)
        sys.exit(1)


@security.group()
def audit():
    """Audit logging commands"""
    pass


@audit.command()
@click.option('--db-url', required=True, help='Database URL')
@click.option('--tenant-id', help='Filter by tenant ID')
@click.option('--extension-name', help='Filter by extension name')
@click.option('--days', default=7, help='Number of days to look back')
@click.option('--output', type=click.File('w'), default='-', help='Output file (default: stdout)')
def logs(db_url: str, tenant_id: Optional[str], extension_name: Optional[str], 
         days: int, output):
    """Export audit logs"""
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        audit_logger = ExtensionAuditLogger(session)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        logs = audit_logger.get_audit_logs(
            tenant_id=tenant_id,
            extension_name=extension_name,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        # Convert to JSON
        logs_data = [log.dict() for log in logs]
        json.dump(logs_data, output, indent=2, default=str)
        
        click.echo(f"Exported {len(logs)} audit log entries", err=True)
        
    except Exception as e:
        click.echo(f"Error exporting audit logs: {e}", err=True)
        sys.exit(1)


@audit.command()
@click.option('--db-url', required=True, help='Database URL')
@click.option('--tenant-id', required=True, help='Tenant ID')
@click.option('--report-type', 
              type=click.Choice(['security', 'data_protection', 'access_control', 'general']),
              default='security', help='Report type')
@click.option('--days', default=30, help='Number of days to analyze')
@click.option('--output', type=click.File('w'), default='-', help='Output file (default: stdout)')
def compliance_report(db_url: str, tenant_id: str, report_type: str, days: int, output):
    """Generate compliance report"""
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        audit_logger = ExtensionAuditLogger(session)
        compliance_reporter = ExtensionComplianceReporter(session, audit_logger)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        report = compliance_reporter.generate_compliance_report(
            tenant_id=tenant_id,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        
        json.dump(report.dict(), output, indent=2, default=str)
        
        click.echo(f"Generated {report_type} compliance report for tenant {tenant_id}", err=True)
        click.echo(f"Compliance score: {report.compliance_score:.1f}%", err=True)
        
    except Exception as e:
        click.echo(f"Error generating compliance report: {e}", err=True)
        sys.exit(1)


@security.group()
def scan():
    """Vulnerability scanning commands"""
    pass


@scan.command()
@click.option('--extension-path', required=True, help='Path to extension directory')
@click.option('--extension-name', required=True, help='Extension name')
@click.option('--extension-version', required=True, help='Extension version')
@click.option('--scan-types', default='code,dependencies,permissions', 
              help='Comma-separated scan types')
@click.option('--deep-scan', is_flag=True, help='Perform deep security scan')
@click.option('--db-url', help='Database URL to store results')
@click.option('--output', type=click.File('w'), default='-', help='Output file (default: stdout)')
def vulnerability(extension_path: str, extension_name: str, extension_version: str,
                 scan_types: str, deep_scan: bool, db_url: Optional[str], output):
    """Scan extension for vulnerabilities"""
    try:
        # Parse scan types
        scan_types_list = [t.strip() for t in scan_types.split(',')]
        
        scan_request = SecurityScanRequest(
            extension_name=extension_name,
            extension_version=extension_version,
            scan_types=scan_types_list,
            deep_scan=deep_scan
        )
        
        # Initialize scanner
        if db_url:
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            audit_logger = ExtensionAuditLogger(session)
            scanner = ExtensionVulnerabilityScanner(session, audit_logger)
        else:
            scanner = ExtensionVulnerabilityScanner(None)
        
        # Perform scan
        result = scanner.scan_extension(
            extension_path=Path(extension_path),
            extension_name=extension_name,
            extension_version=extension_version,
            scan_request=scan_request
        )
        
        # Output results
        json.dump(result.dict(), output, indent=2, default=str)
        
        # Summary to stderr
        click.echo(f"Scan completed for {extension_name} v{extension_version}", err=True)
        click.echo(f"Vulnerabilities found: {len(result.vulnerabilities)}", err=True)
        click.echo(f"Security score: {result.security_score:.1f}%", err=True)
        
        # Exit with error code if critical vulnerabilities found
        critical_vulns = [v for v in result.vulnerabilities if v.severity.value == 'critical']
        if critical_vulns:
            click.echo(f"CRITICAL: {len(critical_vulns)} critical vulnerabilities found!", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error scanning extension: {e}", err=True)
        sys.exit(1)


@security.group()
def access():
    """Access control commands"""
    pass


@access.command()
@click.option('--db-url', required=True, help='Database URL')
@click.option('--extension-name', help='Filter by extension name')
@click.option('--tenant-id', help='Filter by tenant ID')
@click.option('--output', type=click.File('w'), default='-', help='Output file (default: stdout)')
def list_policies(db_url: str, extension_name: Optional[str], tenant_id: Optional[str], output):
    """List access control policies"""
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        access_manager = ExtensionAccessControlManager(session)
        
        policies = access_manager.list_policies(extension_name, tenant_id)
        
        policies_data = [policy.dict() for policy in policies]
        json.dump(policies_data, output, indent=2, default=str)
        
        click.echo(f"Listed {len(policies)} access control policies", err=True)
        
    except Exception as e:
        click.echo(f"Error listing policies: {e}", err=True)
        sys.exit(1)


@security.command()
@click.option('--db-url', required=True, help='Database URL')
def init_db(db_url: str):
    """Initialize security database tables"""
    try:
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        
        click.echo("Security database tables initialized successfully")
        
    except Exception as e:
        click.echo(f"Error initializing database: {e}", err=True)
        sys.exit(1)


@security.command()
@click.option('--db-url', required=True, help='Database URL')
@click.option('--tenant-id', required=True, help='Tenant ID')
@click.option('--days', default=7, help='Number of days to analyze')
def security_dashboard(db_url: str, tenant_id: str, days: int):
    """Display security dashboard summary"""
    try:
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        audit_logger = ExtensionAuditLogger(session)
        scanner = ExtensionVulnerabilityScanner(session)
        
        # Get audit summary
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        audit_summary = audit_logger.get_audit_summary(tenant_id, start_date, end_date)
        
        # Get vulnerability summary
        all_vulns = scanner.get_vulnerabilities()
        open_vulns = [v for v in all_vulns if v.status == 'open']
        critical_vulns = [v for v in open_vulns if v.severity == 'critical']
        
        # Display dashboard
        click.echo("=" * 50)
        click.echo(f"SECURITY DASHBOARD - Tenant: {tenant_id}")
        click.echo("=" * 50)
        click.echo()
        
        click.echo("AUDIT SUMMARY (Last {} days):".format(days))
        click.echo(f"  Total Events: {audit_summary['total_events']}")
        click.echo(f"  High Risk Events: {audit_summary['high_risk_events']}")
        click.echo()
        
        click.echo("VULNERABILITY SUMMARY:")
        click.echo(f"  Total Vulnerabilities: {len(all_vulns)}")
        click.echo(f"  Open Vulnerabilities: {len(open_vulns)}")
        click.echo(f"  Critical Vulnerabilities: {len(critical_vulns)}")
        click.echo()
        
        security_score = max(100 - len(critical_vulns) * 20 - len(open_vulns) * 5, 0)
        click.echo(f"SECURITY SCORE: {security_score:.1f}%")
        
        if critical_vulns:
            click.echo()
            click.echo("⚠️  CRITICAL VULNERABILITIES REQUIRE IMMEDIATE ATTENTION!")
        
    except Exception as e:
        click.echo(f"Error generating security dashboard: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    security()