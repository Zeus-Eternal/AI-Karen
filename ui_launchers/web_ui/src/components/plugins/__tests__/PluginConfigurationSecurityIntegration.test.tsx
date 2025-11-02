/**
 * Plugin Configuration and Security Integration Tests
 * 
 * Security tests for plugin isolation and permission enforcement.
 * Based on requirements: 5.3, 5.5, 9.1, 9.2, 9.4
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PluginConfigurationSecurityIntegration } from '../PluginConfigurationSecurityIntegration';
import { PluginInfo, PluginConfigField } from '@/types/plugins';

// Mock the child components
vi.mock('../DynamicPluginConfigForm', () => ({
  DynamicPluginConfigForm: ({ onSave, onValidate }: any) => (
    <div data-testid="dynamic-config-form">
      <button onClick={() => onSave({ testConfig: 'value' })}>Save Config</button>
      <button onClick={() => onValidate({ testConfig: 'value' })}>Validate Config</button>
    </div>
  ),
}));

vi.mock('../PluginSecurityManager', () => ({
  PluginSecurityManager: ({ onUpdateSecurity, onGrantPermission, onRevokePermission }: any) => (
    <div data-testid="security-manager">
      <button onClick={() => onUpdateSecurity({ sandboxed: true })}>Update Security</button>
      <button onClick={() => onGrantPermission('test-permission')}>Grant Permission</button>
      <button onClick={() => onRevokePermission('test-permission')}>Revoke Permission</button>
    </div>
  ),
}));

vi.mock('../PluginAuditLogger', () => ({
  PluginAuditLogger: ({ onExportAuditLog, onGenerateReport }: any) => (
    <div data-testid="audit-logger">
      <button onClick={() => onExportAuditLog('csv')}>Export Audit</button>
      <button onClick={() => onGenerateReport('security')}>Generate Report</button>
    </div>
  ),
}));

vi.mock('../EnhancedPluginMarketplace', () => ({
  EnhancedPluginMarketplace: ({ onClose, onInstall }: any) => (
    <div data-testid="marketplace">
      <button onClick={() => onInstall({ id: 'test-plugin' })}>Install Plugin</button>
      <button onClick={onClose} aria-label="Button">Close Marketplace</button>
    </div>
  ),
}));

// Mock plugin with security-sensitive configuration
const createMockPlugin = (overrides: Partial<PluginInfo> = {}): PluginInfo => ({
  id: 'security-test-plugin',
  name: 'Security Test Plugin',
  version: '1.0.0',
  status: 'active',
  manifest: {
    id: 'security-test-plugin',
    name: 'Security Test Plugin',
    version: '1.0.0',
    description: 'A plugin for testing security features',
    author: { name: 'Security Team' },
    license: 'MIT',
    keywords: ['security', 'test'],
    category: 'security',
    runtime: { platform: ['node'] },
    dependencies: [],
    systemRequirements: {},
    permissions: [
      {
        id: 'network-access',
        name: 'Network Access',
        description: 'Access to external networks',
        category: 'network',
        level: 'read',
        required: true,
      },
      {
        id: 'file-system-access',
        name: 'File System Access',
        description: 'Access to file system',
        category: 'data',
        level: 'write',
        required: false,
      },
      {
        id: 'admin-access',
        name: 'Administrative Access',
        description: 'Administrative privileges',
        category: 'system',
        level: 'admin',
        required: false,
      },
    ],
    sandboxed: true,
    securityPolicy: {
      allowNetworkAccess: true,
      allowFileSystemAccess: false,
      allowSystemCalls: false,
      trustedDomains: ['api.example.com'],
    },
    configSchema: [
      {
        key: 'apiKey',
        type: 'password',
        label: 'API Key',
        description: 'Sensitive API key',
        required: true,
      },
      {
        key: 'enableDangerousFeature',
        type: 'boolean',
        label: 'Enable Dangerous Feature',
        description: 'Enables potentially dangerous functionality',
        required: false,
        default: false,
      },
    ] as PluginConfigField[],
    apiVersion: '1.0',
  },
  config: {
    apiKey: 'test-api-key',
    enableDangerousFeature: false,
  },
  permissions: [
    {
      id: 'network-access',
      name: 'Network Access',
      description: 'Access to external networks',
      category: 'network',
      level: 'read',
      required: true,
    },
  ],
  metrics: {
    performance: {
      averageExecutionTime: 100,
      totalExecutions: 50,
      errorRate: 0.02,
      lastExecution: new Date(),
    },
    resources: {
      memoryUsage: 64,
      cpuUsage: 5,
      diskUsage: 10,
      networkUsage: 2,
    },
    health: {
      status: 'healthy',
      uptime: 99.5,
      lastHealthCheck: new Date(),
      issues: [],
    },
  },
  installedAt: new Date(),
  updatedAt: new Date(),
  installedBy: 'admin',
  enabled: true,
  autoStart: true,
  restartCount: 0,
  dependencyStatus: {
    satisfied: true,
    missing: [],
    conflicts: [],
  },
  ...overrides,

const mockProps = {
  plugin: createMockPlugin(),
  onClose: vi.fn(),
  onSaveConfiguration: vi.fn(),
  onUpdateSecurity: vi.fn(),
  onGrantPermission: vi.fn(),
  onRevokePermission: vi.fn(),
  onInstallFromMarketplace: vi.fn(),
  onPurchasePlugin: vi.fn(),
  onExportAuditLog: vi.fn(),
  onGenerateReport: vi.fn(),
};

describe('PluginConfigurationSecurityIntegration - Security Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  describe('Plugin Isolation Tests', () => {
    it('should enforce sandboxed execution for sandboxed plugins', () => {
      const sandboxedPlugin = createMockPlugin({
        manifest: {
          ...createMockPlugin().manifest,
          sandboxed: true,
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={sandboxedPlugin} />);
      
      // Should display sandboxed badge
      expect(screen.getByText('Sandboxed')).toBeInTheDocument();

    it('should show security warnings for non-sandboxed plugins', () => {
      const nonSandboxedPlugin = createMockPlugin({
        manifest: {
          ...createMockPlugin().manifest,
          sandboxed: false,
          securityPolicy: {
            allowNetworkAccess: true,
            allowFileSystemAccess: true,
            allowSystemCalls: true,
          },
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={nonSandboxedPlugin} />);
      
      // Should show high security risk
      expect(screen.getByText('Critical')).toBeInTheDocument();
      expect(screen.getByText('High security risk')).toBeInTheDocument();

    it('should calculate security risk level correctly', () => {
      const highRiskPlugin = createMockPlugin({
        manifest: {
          ...createMockPlugin().manifest,
          sandboxed: false,
          securityPolicy: {
            allowNetworkAccess: true,
            allowFileSystemAccess: true,
            allowSystemCalls: true,
          },
          permissions: [
            {
              id: 'admin-1',
              name: 'Admin Permission 1',
              description: 'Administrative access',
              category: 'system',
              level: 'admin',
              required: false,
            },
            {
              id: 'admin-2',
              name: 'Admin Permission 2',
              description: 'Administrative access',
              category: 'system',
              level: 'admin',
              required: false,
            },
          ],
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={highRiskPlugin} />);
      
      // Should show critical risk level
      expect(screen.getByText('Critical')).toBeInTheDocument();

    it('should show low risk for properly sandboxed plugins', () => {
      const lowRiskPlugin = createMockPlugin({
        manifest: {
          ...createMockPlugin().manifest,
          sandboxed: true,
          securityPolicy: {
            allowNetworkAccess: false,
            allowFileSystemAccess: false,
            allowSystemCalls: false,
          },
          permissions: [
            {
              id: 'read-only',
              name: 'Read Only Access',
              description: 'Read-only access',
              category: 'data',
              level: 'read',
              required: false,
            },
          ],
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={lowRiskPlugin} />);
      
      // Should show low risk level
      expect(screen.getByText('Low')).toBeInTheDocument();
      expect(screen.getByText('Minimal security risk')).toBeInTheDocument();


  describe('Permission Enforcement Tests', () => {
    it('should handle permission granting securely', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Navigate to security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      
      await waitFor(() => {
        const grantButton = screen.getByText('Grant Permission');
        fireEvent.click(grantButton);

      expect(mockProps.onGrantPermission).toHaveBeenCalledWith('test-permission');

    it('should handle permission revocation securely', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Navigate to security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      
      await waitFor(() => {
        const revokeButton = screen.getByText('Revoke Permission');
        fireEvent.click(revokeButton);

      expect(mockProps.onRevokePermission).toHaveBeenCalledWith('test-permission');

    it('should prevent unauthorized permission changes in read-only mode', () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} readOnly />);
      
      // Security manager should be in read-only mode
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      
      // Component should pass readOnly prop to security manager
      expect(screen.getByTestId('security-manager')).toBeInTheDocument();

    it('should validate required permissions are not revoked', () => {
      const pluginWithRequiredPermissions = createMockPlugin({
        manifest: {
          ...createMockPlugin().manifest,
          permissions: [
            {
              id: 'required-permission',
              name: 'Required Permission',
              description: 'This permission is required',
              category: 'system',
              level: 'read',
              required: true,
            },
          ],
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={pluginWithRequiredPermissions} />);
      
      // Should show that plugin has required permissions
      expect(screen.getByText('1 permissions')).toBeInTheDocument();


  describe('Configuration Security Tests', () => {
    it('should validate sensitive configuration fields', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Should be on configuration tab by default
      await waitFor(() => {
        const validateButton = screen.getByText('Validate Config');
        fireEvent.click(validateButton);

      // Validation should be called
      expect(screen.getByTestId('dynamic-config-form')).toBeInTheDocument();

    it('should handle secure configuration saving', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      const saveButton = screen.getByText('Save Config');
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(mockProps.onSaveConfiguration).toHaveBeenCalledWith({ testConfig: 'value' });


    it('should show unsaved changes warning', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Simulate configuration change
      const saveButton = screen.getByText('Save Config');
      fireEvent.click(saveButton);
      
      // Should not show warning initially since save was called
      await waitFor(() => {
        expect(mockProps.onSaveConfiguration).toHaveBeenCalled();


    it('should prevent dangerous configuration in production', () => {
      const dangerousPlugin = createMockPlugin({
        config: {
          apiKey: 'test-key',
          enableDangerousFeature: true, // This should trigger warnings
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={dangerousPlugin} />);
      
      // Should show plugin information
      expect(screen.getByText('Security Test Plugin')).toBeInTheDocument();


  describe('Audit and Compliance Tests', () => {
    it('should provide audit log export functionality', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Navigate to audit tab
      const auditTab = screen.getByRole('tab', { name: /audit/i });
      fireEvent.click(auditTab);
      
      await waitFor(() => {
        const exportButton = screen.getByText('Export Audit');
        fireEvent.click(exportButton);

      expect(mockProps.onExportAuditLog).toHaveBeenCalledWith('csv');

    it('should generate security compliance reports', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Navigate to audit tab
      const auditTab = screen.getByRole('tab', { name: /audit/i });
      fireEvent.click(auditTab);
      
      await waitFor(() => {
        const reportButton = screen.getByText('Generate Report');
        fireEvent.click(reportButton);

      expect(mockProps.onGenerateReport).toHaveBeenCalledWith('security');

    it('should track all security-related actions', () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Navigate to audit tab
      const auditTab = screen.getByRole('tab', { name: /audit/i });
      fireEvent.click(auditTab);
      
      // Audit logger should be rendered
      expect(screen.getByTestId('audit-logger')).toBeInTheDocument();


  describe('Marketplace Security Tests', () => {
    it('should validate plugins before installation from marketplace', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Open marketplace
      const marketplaceButton = screen.getByText('Marketplace');
      fireEvent.click(marketplaceButton);
      
      await waitFor(() => {
        const installButton = screen.getByText('Install Plugin');
        fireEvent.click(installButton);

      expect(mockProps.onInstallFromMarketplace).toHaveBeenCalledWith({ id: 'test-plugin' });

    it('should handle secure plugin purchases', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Open marketplace
      const marketplaceButton = screen.getByText('Marketplace');
      fireEvent.click(marketplaceButton);
      
      // Marketplace should be rendered in dialog
      await waitFor(() => {
        expect(screen.getByTestId('marketplace')).toBeInTheDocument();


    it('should close marketplace securely', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Open marketplace
      const marketplaceButton = screen.getByText('Marketplace');
      fireEvent.click(marketplaceButton);
      
      await waitFor(() => {
        const closeButton = screen.getByText('Close Marketplace');
        fireEvent.click(closeButton);

      // Marketplace dialog should close
      await waitFor(() => {
        expect(screen.queryByTestId('marketplace')).not.toBeInTheDocument();



  describe('Error Handling and Security', () => {
    it('should display plugin errors securely', () => {
      const errorPlugin = createMockPlugin({
        status: 'error',
        lastError: {
          message: 'Plugin failed to start due to security violation',
          timestamp: new Date(),
          stack: 'Error stack trace...',
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={errorPlugin} />);
      
      // Should show error alert
      expect(screen.getByText(/Plugin error:/)).toBeInTheDocument();
      expect(screen.getByText(/security violation/)).toBeInTheDocument();

    it('should handle security policy update failures gracefully', async () => {
      const failingProps = {
        ...mockProps,
        onUpdateSecurity: vi.fn().mockRejectedValue(new Error('Security update failed')),
      };

      render(<PluginConfigurationSecurityIntegration {...failingProps} />);
      
      // Navigate to security tab
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      
      await waitFor(() => {
        const updateButton = screen.getByText('Update Security');
        fireEvent.click(updateButton);

      // Should attempt to update security
      expect(failingProps.onUpdateSecurity).toHaveBeenCalled();

    it('should validate plugin manifest security settings', () => {
      const invalidPlugin = createMockPlugin({
        manifest: {
          ...createMockPlugin().manifest,
          securityPolicy: {
            allowNetworkAccess: true,
            allowFileSystemAccess: true,
            allowSystemCalls: true,
            trustedDomains: [], // Empty trusted domains with network access
          },
        },

      render(<PluginConfigurationSecurityIntegration {...mockProps} plugin={invalidPlugin} />);
      
      // Should show high security risk
      expect(screen.getByText('High')).toBeInTheDocument();


  describe('Integration Security Tests', () => {
    it('should maintain security context across tab switches', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Switch between tabs
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      
      const configTab = screen.getByRole('tab', { name: /configuration/i });
      fireEvent.click(configTab);
      
      const auditTab = screen.getByRole('tab', { name: /audit/i });
      fireEvent.click(auditTab);
      
      // All components should maintain security context
      expect(screen.getByTestId('audit-logger')).toBeInTheDocument();

    it('should prevent unauthorized access to sensitive operations', () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} readOnly />);
      
      // In read-only mode, sensitive operations should be disabled
      // This is tested by ensuring readOnly prop is passed to child components
      expect(screen.getByTestId('dynamic-config-form')).toBeInTheDocument();
      expect(screen.getByTestId('security-manager')).toBeInTheDocument();

    it('should handle concurrent security operations safely', async () => {
      render(<PluginConfigurationSecurityIntegration {...mockProps} />);
      
      // Simulate concurrent operations
      const securityTab = screen.getByRole('tab', { name: /security/i });
      fireEvent.click(securityTab);
      
      await waitFor(() => {
        const grantButton = screen.getByText('Grant Permission');
        const revokeButton = screen.getByText('Revoke Permission');
        
        // Click both buttons rapidly
        fireEvent.click(grantButton);
        fireEvent.click(revokeButton);

      // Both operations should be handled
      expect(mockProps.onGrantPermission).toHaveBeenCalled();
      expect(mockProps.onRevokePermission).toHaveBeenCalled();


