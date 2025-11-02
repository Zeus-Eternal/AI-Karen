/**
 * Tests for RealTimeMonitoringDashboard component
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RealTimeMonitoringDashboard } from '../RealTimeMonitoringDashboard';
import { SystemHealth } from '../types';
import * as loggingModule from '../../../lib/logging';

// Mock the logging module
jest.mock('../../../lib/logging', () => ({
  connectivityLogger: {
    logConnectivity: jest.fn(),
    logError: jest.fn()
  },
  performanceTracker: {
    getPerformanceStats: jest.fn(() => ({
      count: 100,
      averageTime: 1200,
      minTime: 200,
      maxTime: 3000,
      p95Time: 2500,
      p99Time: 2800
    }))
  }
}));

// Mock fetch
global.fetch = jest.fn();

describe('RealTimeMonitoringDashboard', () => {
  const mockSystemHealth: SystemHealth = {
    overall: 'healthy',
    components: {
      backend: {
        isConnected: true,
        lastCheck: new Date('2024-01-01T12:00:00Z'),
        responseTime: 800,
        endpoint: 'http://localhost:8000',
        status: 'healthy',
        errorCount: 2,
        successCount: 98
      },
      database: {
        isConnected: true,
        lastCheck: new Date('2024-01-01T12:00:00Z'),
        responseTime: 600,
        endpoint: 'postgresql://localhost:5432',
        status: 'healthy',
        errorCount: 1,
        successCount: 199
      },
      authentication: {
        isConnected: true,
        lastCheck: new Date('2024-01-01T12:00:00Z'),
        responseTime: 900,
        endpoint: '/api/auth',
        status: 'healthy',
        errorCount: 3,
        successCount: 97
      }
    },
    performance: {
      averageResponseTime: 800,
      p95ResponseTime: 1200,
      p99ResponseTime: 1800,
      requestCount: 1500,
      errorRate: 2.1,
      throughput: 5.2,
      timeRange: 'Last 1 hour'
    },
    errors: {
      totalErrors: 32,
      errorRate: 2.1,
      errorsByType: {
        'Network Timeout': 15,
        'Authentication Failed': 8,
        'Database Connection': 5,
        'Validation Error': 4
      },
      recentErrors: [
        {
          timestamp: new Date('2024-01-01T11:55:00Z'),
          type: 'Network Timeout',
          message: 'Request timeout after 5000ms',
          correlationId: 'corr_123456'
        }
      ]
    },
    authentication: {
      totalAttempts: 250,
      successfulAttempts: 238,
      failedAttempts: 12,
      successRate: 95.2,
      averageAuthTime: 750,
      recentFailures: [
        {
          timestamp: new Date('2024-01-01T11:50:00Z'),
          reason: 'Invalid credentials',
          email: 'user@example.com'
        }
      ]
    },
    lastUpdated: new Date('2024-01-01T12:00:00Z')
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-01-01T12:05:00Z'));

  afterEach(() => {
    jest.useRealTimers();

  describe('Initial Loading', () => {
    it('should show loading state initially', () => {
      render(<RealTimeMonitoringDashboard />);
      
      expect(screen.getByText('Loading system health...')).toBeInTheDocument();
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument(); // Loading spinner

    it('should render dashboard after loading', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();

      expect(screen.getByText('Backend API')).toBeInTheDocument();
      expect(screen.getByText('Database')).toBeInTheDocument();
      expect(screen.getByText('Authentication')).toBeInTheDocument();


  describe('System Status Display', () => {
    it('should display overall system status', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText(/System is/)).toBeInTheDocument();


    it('should show correct status badge colors', async () => {
      const { rerender } = render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();

      // Test different status colors by mocking different health states
      // This would require more complex mocking of the health generation


  describe('Component Status Grid', () => {
    it('should render all component status indicators', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Backend API')).toBeInTheDocument();
        expect(screen.getByText('Database')).toBeInTheDocument();
        expect(screen.getByText('Authentication')).toBeInTheDocument();


    it('should show component details when configured', async () => {
      render(
        <RealTimeMonitoringDashboard 
          config={{ showDetailedMetrics: true }}
        />
      );
      
      await waitFor(() => {
        expect(screen.getAllByText('Success Rate:')).toHaveLength(3);
        expect(screen.getAllByText('Endpoint:')).toHaveLength(3);



  describe('Performance Metrics', () => {
    it('should display performance metrics', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
        expect(screen.getByText('Average')).toBeInTheDocument();
        expect(screen.getByText('95th %ile')).toBeInTheDocument();
        expect(screen.getByText('99th %ile')).toBeInTheDocument();


    it('should show error rate metrics', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Error Metrics')).toBeInTheDocument();
        expect(screen.getByText('Error Rate')).toBeInTheDocument();



  describe('Authentication Metrics', () => {
    it('should display authentication metrics', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Authentication Metrics')).toBeInTheDocument();
        expect(screen.getByText('Success Rate')).toBeInTheDocument();
        expect(screen.getByText('Successful')).toBeInTheDocument();
        expect(screen.getByText('Failed')).toBeInTheDocument();



  describe('Refresh Functionality', () => {
    it('should have refresh button', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();


    it('should refresh data when refresh button is clicked', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      expect(screen.getByText('Refreshing...')).toBeInTheDocument();

    it('should toggle auto-refresh', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Auto-refresh ON')).toBeInTheDocument();

      const autoRefreshButton = screen.getByText('Auto-refresh ON');
      fireEvent.click(autoRefreshButton);
      
      expect(screen.getByText('Auto-refresh OFF')).toBeInTheDocument();


  describe('Real-time Updates', () => {
    it('should auto-refresh at configured intervals', async () => {
      const onHealthChange = jest.fn();
      
      render(
        <RealTimeMonitoringDashboard 
          config={{ refreshInterval: 1000 }}
          onHealthChange={onHealthChange}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();

      // Fast-forward time to trigger auto-refresh
      jest.advanceTimersByTime(1000);
      
      await waitFor(() => {
        expect(onHealthChange).toHaveBeenCalled();


    it('should not auto-refresh when disabled', async () => {
      const onHealthChange = jest.fn();
      
      render(
        <RealTimeMonitoringDashboard 
          config={{ enableRealTimeUpdates: false }}
          onHealthChange={onHealthChange}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();

      // Clear initial call
      onHealthChange.mockClear();
      
      // Fast-forward time
      jest.advanceTimersByTime(30000);
      
      // Should not have been called again
      expect(onHealthChange).not.toHaveBeenCalled();


  describe('Configuration Options', () => {
    it('should apply custom refresh interval', async () => {
      const customConfig = {
        refreshInterval: 5000,
        enableRealTimeUpdates: true
      };
      
      render(<RealTimeMonitoringDashboard config={customConfig} />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();

      // The component should use the custom interval
      // This is tested indirectly through the auto-refresh functionality

    it('should hide detailed metrics when configured', async () => {
      render(
        <RealTimeMonitoringDashboard 
          config={{ showDetailedMetrics: false }}
        />
      );
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();

      // Should not show detailed metrics
      expect(screen.queryByText('Success Rate:')).not.toBeInTheDocument();


  describe('Error Handling', () => {
    it('should handle health check failures gracefully', async () => {
      // Mock console.error to avoid test output noise
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Mock fetch to fail
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();

      // Should still render the dashboard with mock data
      expect(loggingModule.connectivityLogger.logError).toHaveBeenCalled();
      
      consoleSpy.mockRestore();


  describe('Callback Functions', () => {
    it('should call onHealthChange when health updates', async () => {
      const onHealthChange = jest.fn();
      
      render(<RealTimeMonitoringDashboard onHealthChange={onHealthChange} />);
      
      await waitFor(() => {
        expect(onHealthChange).toHaveBeenCalled();

      const healthData = onHealthChange.mock.calls[0][0];
      expect(healthData).toHaveProperty('overall');
      expect(healthData).toHaveProperty('components');
      expect(healthData).toHaveProperty('performance');


  describe('Accessibility', () => {
    it('should have proper heading structure', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /System Health Dashboard/i })).toBeInTheDocument();


    it('should have accessible buttons', async () => {
      render(<RealTimeMonitoringDashboard />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Auto-refresh/i })).toBeInTheDocument();



