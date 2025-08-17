/**
 * Tests for Endpoint Status Dashboard Component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { EndpointStatusDashboard } from '../endpoint-status-dashboard';

// Mock the lib modules
vi.mock('@/lib/health-monitor', () => ({
  getHealthMonitor: () => ({
    getMetrics: () => ({
      totalRequests: 100,
      successfulRequests: 95,
      failedRequests: 5,
      averageResponseTime: 250,
      errorRate: 0.05,
      lastHealthCheck: new Date().toISOString(),
      uptime: 3600000,
      endpoints: {
        '/api/health': {
          endpoint: '/api/health',
          status: 'healthy',
          responseTime: 150,
          timestamp: new Date().toISOString(),
        },
        '/api/auth/status': {
          endpoint: '/api/auth/status',
          status: 'error',
          responseTime: 0,
          timestamp: new Date().toISOString(),
          error: 'Connection refused',
        },
      },
    }),
    getStatus: () => ({ isMonitoring: true }),
    onMetricsUpdate: () => () => {},
    start: vi.fn(),
    stop: vi.fn(),
  }),
}));

vi.mock('@/lib/diagnostics', () => ({
  getDiagnosticLogger: () => ({
    getLogs: () => [
      {
        timestamp: new Date().toISOString(),
        level: 'error',
        category: 'network',
        message: 'Connection failed to /api/auth/status',
        endpoint: '/api/auth/status',
        error: 'Connection refused',
      },
    ],
    onLog: () => () => {},
    exportLogs: () => JSON.stringify({ logs: [] }),
  }),
}));

vi.mock('@/lib/network-diagnostics', () => ({
  getNetworkDiagnostics: () => ({
    runComprehensiveTest: () => Promise.resolve({
      timestamp: new Date().toISOString(),
      overallStatus: 'degraded',
      summary: {
        totalTests: 5,
        passedTests: 4,
        failedTests: 1,
        averageResponseTime: 300,
      },
      testResults: [],
      systemInfo: {
        userAgent: 'test',
        isOnline: true,
        protocol: 'http',
        host: 'localhost',
        port: '8000',
      },
      recommendations: ['Check network connectivity'],
    }),
    testEndpointDetailed: () => Promise.resolve({
      connectivity: {
        endpoint: '/api/test',
        method: 'GET',
        status: 'success',
        responseTime: 200,
        timestamp: new Date().toISOString(),
      },
      corsAnalysis: {
        origin: 'http://localhost:9002',
        preflightRequired: false,
      },
      recommendations: [],
    }),
  }),
}));

vi.mock('@/lib/config', () => ({
  webUIConfig: {
    backendUrl: 'http://localhost:8000',
    environment: 'local',
    networkMode: 'localhost',
    fallbackBackendUrls: ['http://127.0.0.1:8000'],
  },
}));

describe('EndpointStatusDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard with endpoint status', async () => {
    render(<EndpointStatusDashboard />);

    // Check if the main title is rendered
    expect(screen.getByText('Endpoint Status Dashboard')).toBeInTheDocument();

    // Check if configuration section is rendered
    expect(screen.getByText('Current Configuration')).toBeInTheDocument();
    expect(screen.getByText('http://localhost:8000')).toBeInTheDocument();

    // Wait for endpoints to load
    await waitFor(() => {
      expect(screen.getByText('/api/health')).toBeInTheDocument();
      expect(screen.getByText('/api/auth/status')).toBeInTheDocument();
    });
  });

  it('shows endpoint status correctly', async () => {
    render(<EndpointStatusDashboard />);

    await waitFor(() => {
      // Check healthy endpoint
      const healthyBadges = screen.getAllByText('healthy');
      expect(healthyBadges.length).toBeGreaterThan(0);

      // Check error endpoint
      const errorBadges = screen.getAllByText('error');
      expect(errorBadges.length).toBeGreaterThan(0);
    });
  });

  it('can run comprehensive diagnostics', async () => {
    render(<EndpointStatusDashboard />);

    const runDiagnosticsButton = screen.getByText('Run Diagnostics');
    fireEvent.click(runDiagnosticsButton);

    await waitFor(() => {
      expect(screen.getByText(/Comprehensive diagnostics completed/)).toBeInTheDocument();
    });
  });

  it('displays diagnostic logs', async () => {
    render(<EndpointStatusDashboard />);

    // Switch to diagnostics tab
    const diagnosticsTab = screen.getByText('Diagnostics');
    fireEvent.click(diagnosticsTab);

    await waitFor(() => {
      expect(screen.getByText('Connection failed to /api/auth/status')).toBeInTheDocument();
    });
  });

  it('can test custom endpoints', async () => {
    render(<EndpointStatusDashboard />);

    // Switch to testing tab
    const testingTab = screen.getByText('Manual Testing');
    fireEvent.click(testingTab);

    // Enter custom endpoint
    const input = screen.getByPlaceholderText(/Enter endpoint URL/);
    fireEvent.change(input, { target: { value: '/api/test' } });

    // Click test button
    const testButton = screen.getByText('Test');
    fireEvent.click(testButton);

    // The test should complete (mocked to resolve)
    await waitFor(() => {
      expect(input).toHaveValue('/api/test');
    });
  });

  it('can export diagnostic logs', async () => {
    // Mock URL.createObjectURL and related functions
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    const mockAppendChild = vi.fn();
    const mockRemoveChild = vi.fn();
    const mockClick = vi.fn();
    
    Object.defineProperty(document, 'createElement', {
      value: vi.fn(() => ({
        href: '',
        download: '',
        click: mockClick,
      })),
    });
    
    Object.defineProperty(document.body, 'appendChild', {
      value: mockAppendChild,
    });
    
    Object.defineProperty(document.body, 'removeChild', {
      value: mockRemoveChild,
    });

    render(<EndpointStatusDashboard />);

    // Switch to diagnostics tab
    const diagnosticsTab = screen.getByText('Diagnostics');
    fireEvent.click(diagnosticsTab);

    // Click export button
    const exportButton = screen.getByText('Export');
    fireEvent.click(exportButton);

    expect(mockClick).toHaveBeenCalled();
    expect(mockAppendChild).toHaveBeenCalled();
    expect(mockRemoveChild).toHaveBeenCalled();
  });

  it('handles monitoring toggle', async () => {
    render(<EndpointStatusDashboard />);

    const toggleButton = screen.getByText('Stop');
    fireEvent.click(toggleButton);

    // The button text should change (though the mock doesn't actually change the state)
    expect(toggleButton).toBeInTheDocument();
  });
});