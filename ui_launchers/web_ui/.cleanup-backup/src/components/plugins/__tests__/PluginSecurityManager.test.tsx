/**
 * Plugin Security Manager Tests
 * 
 * Unit tests for the PluginSecurityManager component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { PluginSecurityManager } from '../PluginSecurityManager';
import { PluginInfo } from '@/types/plugins';

// Mock plugin data
const mockPlugin: PluginInfo = {
  id: 'test-plugin',
  name: 'Test Plugin',
  version: '1.0.0',
  status: 'active',
  manifest: {
    id: 'test-plugin',
    name: 'Test Plugin',
    version: '1.0.0',
    description: 'A test plugin',
    author: { name: 'Test Author' },
    license: 'MIT',
    keywords: ['test'],
    category: 'utility',
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
        id: 'file-access',
        name: 'File Access',
        description: 'Access to file system',
        category: 'data',
        level: 'write',
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
    configSchema: [],
    apiVersion: '1.0',
  },
  config: {},
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
};

const mockProps = {
  plugin: mockPlugin,
  onUpdateSecurity: vi.fn(),
  onGrantPermission: vi.fn(),
  onRevokePermission: vi.fn(),
};

describe('PluginSecurityManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders security overview correctly', () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    expect(screen.getByText('Security Management')).toBeInTheDocument();
    expect(screen.getByText('Security Overview')).toBeInTheDocument();
    expect(screen.getByText('Sandboxed')).toBeInTheDocument();
    expect(screen.getByText('Network Access')).toBeInTheDocument();
  });

  it('displays security score and level', () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    // Security score should be displayed
    expect(screen.getByText(/\d+/)).toBeInTheDocument();
  });

  it('shows permission management tab', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const permissionsTab = screen.getByRole('tab', { name: /permissions/i });
    fireEvent.click(permissionsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Permission Management')).toBeInTheDocument();
      expect(screen.getByText('Network Access')).toBeInTheDocument();
    });
  });

  it('handles permission toggle', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const permissionsTab = screen.getByRole('tab', { name: /permissions/i });
    fireEvent.click(permissionsTab);
    
    await waitFor(() => {
      const switches = screen.getAllByRole('switch');
      if (switches.length > 0) {
        fireEvent.click(switches[0]);
      }
    });
    
    // Should call the appropriate handler
    await waitFor(() => {
      expect(mockProps.onGrantPermission).toHaveBeenCalled() || 
      expect(mockProps.onRevokePermission).toHaveBeenCalled();
    });
  });

  it('shows security policy configuration', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const policyTab = screen.getByRole('tab', { name: /policy/i });
    fireEvent.click(policyTab);
    
    await waitFor(() => {
      expect(screen.getByText('Security Policy')).toBeInTheDocument();
      expect(screen.getByText('Access Controls')).toBeInTheDocument();
    });
  });

  it('handles trusted domain management', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const policyTab = screen.getByRole('tab', { name: /policy/i });
    fireEvent.click(policyTab);
    
    await waitFor(() => {
      expect(screen.getByText('Trusted Domains')).toBeInTheDocument();
      expect(screen.getByText('api.example.com')).toBeInTheDocument();
    });
  });

  it('displays security violations', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const violationsTab = screen.getByRole('tab', { name: /violations/i });
    fireEvent.click(violationsTab);
    
    await waitFor(() => {
      expect(screen.getByText('Security Violations')).toBeInTheDocument();
    });
  });

  it('handles save policy action', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const saveButton = screen.getByRole('button', { name: /save policy/i });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockProps.onUpdateSecurity).toHaveBeenCalled();
    });
  });

  it('respects read-only mode', () => {
    render(<PluginSecurityManager {...mockProps} readOnly />);
    
    const saveButton = screen.queryByRole('button', { name: /save policy/i });
    expect(saveButton).not.toBeInTheDocument();
  });

  it('shows advanced settings when enabled', async () => {
    render(<PluginSecurityManager {...mockProps} />);
    
    const advancedButton = screen.getByRole('button', { name: /advanced/i });
    fireEvent.click(advancedButton);
    
    await waitFor(() => {
      const advancedTab = screen.getByRole('tab', { name: /advanced/i });
      expect(advancedTab).toBeInTheDocument();
    });
  });
});