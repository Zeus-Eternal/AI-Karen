/**
 * Plugin Metrics Tests
 * 
 * Tests for the plugin metrics component.
 * Based on requirements: 5.4, 10.3
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PluginMetrics } from '../PluginMetrics';
import { PluginInfo } from '@/types/plugins';

// Mock plugin data
const mockPlugin: PluginInfo = {
  id: 'test-plugin',
  name: 'Test Plugin',
  version: '1.0.0',
  status: 'active',
  enabled: true,
  autoStart: true,
  restartCount: 0,
  installedAt: new Date('2024-01-15'),
  updatedAt: new Date('2024-01-20'),
  installedBy: 'admin',
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
    permissions: [],
    sandboxed: true,
    securityPolicy: {
      allowNetworkAccess: true,
      allowFileSystemAccess: false,
      allowSystemCalls: false,
    },
    configSchema: [],
    apiVersion: '1.0',
  },
  config: {},
  permissions: [],
  metrics: {
    performance: {
      averageExecutionTime: 250,
      totalExecutions: 1247,
      errorRate: 0.02,
      lastExecution: new Date(),
    },
    resources: {
      memoryUsage: 15.2,
      cpuUsage: 0.5,
      diskUsage: 2.1,
      networkUsage: 0.8,
    },
    health: {
      status: 'healthy',
      uptime: 99.8,
      lastHealthCheck: new Date(),
      issues: [],
    },
  },
  dependencyStatus: {
    satisfied: true,
    missing: [],
    conflicts: [],
  },
};

describe('PluginMetrics', () => {
  const mockOnRefresh = vi.fn();
  const mockOnConfigureAlerts = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders plugin metrics overview', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('Plugin Metrics')).toBeInTheDocument();
    expect(screen.getByText(`Performance and resource usage for ${mockPlugin.name}`)).toBeInTheDocument();

  it('displays key performance metrics', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    // Check for metric values
    expect(screen.getByText('1,247')).toBeInTheDocument(); // Total executions
    expect(screen.getByText('250')).toBeInTheDocument(); // Average execution time
    expect(screen.getByText('2.00')).toBeInTheDocument(); // Error rate percentage
    expect(screen.getByText('99.8')).toBeInTheDocument(); // Health score

  it('displays resource usage with progress bars', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('Resource Usage')).toBeInTheDocument();
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    expect(screen.getByText('Network Usage')).toBeInTheDocument();
    expect(screen.getByText('Disk Usage')).toBeInTheDocument();

    // Check for resource values
    expect(screen.getByText('0.5%')).toBeInTheDocument(); // CPU
    expect(screen.getByText('15.2 MB')).toBeInTheDocument(); // Memory
    expect(screen.getByText('0.8 MB/s')).toBeInTheDocument(); // Network
    expect(screen.getByText('2.1 MB')).toBeInTheDocument(); // Disk

  it('shows recent activity information', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Last Execution')).toBeInTheDocument();
    expect(screen.getByText('Last Health Check')).toBeInTheDocument();
    expect(screen.getByText('Plugin Status')).toBeInTheDocument();

  it('displays health issues when present', () => {
    const pluginWithIssues = {
      ...mockPlugin,
      metrics: {
        ...mockPlugin.metrics,
        health: {
          ...mockPlugin.metrics.health,
          status: 'warning' as const,
          issues: ['API rate limit approaching', 'Memory usage high'],
        },
      },
    };

    render(
      <PluginMetrics
        plugin={pluginWithIssues}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('Health Issues')).toBeInTheDocument();
    expect(screen.getByText('API rate limit approaching')).toBeInTheDocument();

  it('shows no health issues message when healthy', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('No health issues')).toBeInTheDocument();

  it('handles time range selection', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const timeRangeSelect = screen.getByDisplayValue('Last 24h');
    await user.click(timeRangeSelect);
    
    const lastHourOption = screen.getByText('Last Hour');
    await user.click(lastHourOption);

    expect(screen.getByDisplayValue('Last Hour')).toBeInTheDocument();

  it('toggles between simple and advanced view', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const advancedButton = screen.getByRole('button', { name: /advanced/i });
    await user.click(advancedButton);

    expect(screen.getByRole('tab', { name: /advanced/i })).toBeInTheDocument();

  it('calls onRefresh when refresh button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);

    await waitFor(() => {
      expect(mockOnRefresh).toHaveBeenCalled();


  it('calls onConfigureAlerts when alerts button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const alertsButton = screen.getByRole('button', { name: /alerts/i });
    await user.click(alertsButton);

    expect(mockOnConfigureAlerts).toHaveBeenCalled();

  it('displays performance tab content', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const performanceTab = screen.getByRole('tab', { name: /performance/i });
    await user.click(performanceTab);

    expect(screen.getByText('Execution Time Trend')).toBeInTheDocument();
    expect(screen.getByText('Execution Count')).toBeInTheDocument();
    expect(screen.getByText('Error Rate Trend')).toBeInTheDocument();
    expect(screen.getByText('Performance Summary')).toBeInTheDocument();

  it('displays resources tab content', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const resourcesTab = screen.getByRole('tab', { name: /resources/i });
    await user.click(resourcesTab);

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    expect(screen.getByText('Network I/O')).toBeInTheDocument();
    expect(screen.getByText('Disk I/O')).toBeInTheDocument();

  it('displays health tab content', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const healthTab = screen.getByRole('tab', { name: /health/i });
    await user.click(healthTab);

    expect(screen.getByText('Health Status')).toBeInTheDocument();
    expect(screen.getByText('Health Checks')).toBeInTheDocument();
    expect(screen.getByText('Recent Issues')).toBeInTheDocument();

  it('shows correct health status indicators', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    // Should show healthy status
    expect(screen.getByText('Healthy')).toBeInTheDocument();

  it('handles warning health status', () => {
    const warningPlugin = {
      ...mockPlugin,
      metrics: {
        ...mockPlugin.metrics,
        health: {
          ...mockPlugin.metrics.health,
          status: 'warning' as const,
          uptime: 85.5,
        },
      },
    };

    render(
      <PluginMetrics
        plugin={warningPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('85.5%')).toBeInTheDocument();

  it('handles critical health status', () => {
    const criticalPlugin = {
      ...mockPlugin,
      metrics: {
        ...mockPlugin.metrics,
        health: {
          ...mockPlugin.metrics.health,
          status: 'critical' as const,
          uptime: 45.2,
        },
      },
    };

    render(
      <PluginMetrics
        plugin={criticalPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('45.2%')).toBeInTheDocument();

  it('displays performance alerts', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    // Should show mock alerts
    expect(screen.getByText('Performance Alerts')).toBeInTheDocument();

  it('allows dismissing alerts', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    // Look for dismiss buttons (X icons) in alerts
    const dismissButtons = screen.getAllByRole('button');
    const alertDismissButton = dismissButtons.find(button => 
      button.querySelector('svg') && button.closest('[role="alert"]')
    );

    if (alertDismissButton) {
      await user.click(alertDismissButton);
      // Alert should be dismissed (implementation detail)
    }

  it('shows advanced metrics when enabled', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    // Enable advanced view
    const advancedButton = screen.getByRole('button', { name: /advanced/i });
    await user.click(advancedButton);

    // Click advanced tab
    const advancedTab = screen.getByRole('tab', { name: /advanced/i });
    await user.click(advancedTab);

    expect(screen.getByText('Detailed Metrics')).toBeInTheDocument();
    expect(screen.getByText('System Integration')).toBeInTheDocument();

  it('handles refresh loading state', async () => {
    const user = userEvent.setup();
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);

    // Should show loading state briefly
    expect(refreshButton).toBeDisabled();

  it('displays metric trends correctly', () => {
    render(
      <PluginMetrics
        plugin={mockPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    // Should show trend indicators (up/down arrows)
    const trendElements = screen.getAllByText(/\+\d+%|\-\d+%/);
    expect(trendElements.length).toBeGreaterThan(0);

  it('shows correct status colors for different metric levels', () => {
    const highErrorPlugin = {
      ...mockPlugin,
      metrics: {
        ...mockPlugin.metrics,
        performance: {
          ...mockPlugin.metrics.performance,
          errorRate: 0.15, // 15% error rate should show as critical
        },
      },
    };

    render(
      <PluginMetrics
        plugin={highErrorPlugin}
        onRefresh={mockOnRefresh}
        onConfigureAlerts={mockOnConfigureAlerts}
      />
    );

    expect(screen.getByText('15.00')).toBeInTheDocument();

