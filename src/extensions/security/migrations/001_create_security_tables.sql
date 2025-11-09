-- Extension Security Tables Migration
-- Creates tables for enterprise security features

-- Extension signatures table
CREATE TABLE IF NOT EXISTS extension_signatures (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    extension_version VARCHAR(50) NOT NULL,
    signature_hash VARCHAR(512) NOT NULL,
    public_key_id VARCHAR(255) NOT NULL,
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signed_by VARCHAR(255) NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    
    UNIQUE(extension_name, extension_version)
);

-- Extension audit logs table
CREATE TABLE IF NOT EXISTS extension_audit_logs (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    risk_score INTEGER DEFAULT 0
);

-- Extension access policies table
CREATE TABLE IF NOT EXISTS extension_access_policies (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),
    policy_name VARCHAR(255) NOT NULL,
    policy_rules JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(extension_name, tenant_id, policy_name)
);

-- Extension vulnerabilities table
CREATE TABLE IF NOT EXISTS extension_vulnerabilities (
    id SERIAL PRIMARY KEY,
    extension_name VARCHAR(255) NOT NULL,
    extension_version VARCHAR(50) NOT NULL,
    vulnerability_id VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    cve_id VARCHAR(50),
    cvss_score INTEGER,
    status VARCHAR(20) DEFAULT 'open',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fixed_at TIMESTAMP,
    metadata JSONB,
    
    UNIQUE(extension_name, extension_version, vulnerability_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_extension_signatures_name_version 
    ON extension_signatures(extension_name, extension_version);

CREATE INDEX IF NOT EXISTS idx_extension_audit_logs_extension_tenant 
    ON extension_audit_logs(extension_name, tenant_id);

CREATE INDEX IF NOT EXISTS idx_extension_audit_logs_timestamp 
    ON extension_audit_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_extension_audit_logs_event_type 
    ON extension_audit_logs(event_type);

CREATE INDEX IF NOT EXISTS idx_extension_audit_logs_risk_score 
    ON extension_audit_logs(risk_score);

CREATE INDEX IF NOT EXISTS idx_extension_access_policies_extension_tenant 
    ON extension_access_policies(extension_name, tenant_id);

CREATE INDEX IF NOT EXISTS idx_extension_access_policies_active 
    ON extension_access_policies(is_active);

CREATE INDEX IF NOT EXISTS idx_extension_vulnerabilities_extension_version 
    ON extension_vulnerabilities(extension_name, extension_version);

CREATE INDEX IF NOT EXISTS idx_extension_vulnerabilities_severity 
    ON extension_vulnerabilities(severity);

CREATE INDEX IF NOT EXISTS idx_extension_vulnerabilities_status 
    ON extension_vulnerabilities(status);

CREATE INDEX IF NOT EXISTS idx_extension_vulnerabilities_detected_at 
    ON extension_vulnerabilities(detected_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for access policies updated_at
CREATE TRIGGER update_extension_access_policies_updated_at 
    BEFORE UPDATE ON extension_access_policies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();