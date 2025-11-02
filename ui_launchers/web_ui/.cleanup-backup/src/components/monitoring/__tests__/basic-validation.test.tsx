/**
 * Basic validation tests for monitoring components
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConnectionStatusIndicator } from '../ConnectionStatusIndicator';
import { ConnectionStatus } from '../types';

// Mock UI components
vi.mock('../../ui/badge', () => ({
  Badge: ({ children, className }: any) => <span className={className}>{children}</span>
}));

vi.mock('../../ui/card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardHeader: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardTitle: ({ children, className }: any) => <h3 className={className}>{children}</h3>
}));

describe('Monitoring Components Basic Validation', () => {
  const mockHealthyStatus: ConnectionStatus = {
    isConnected: true,
    lastCheck: new Date('2024-01-01T12:00:00Z'),
    responseTime: 500,
    endpoint: 'https://api.example.com',
    status: 'healthy',
    errorCount: 2,
    successCount: 98
  };

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-01-01T12:05:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('ConnectionStatusIndicator', () => {
    it('should render without crashing', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Backend API"
        />
      );

      expect(screen.getByText('Backend API')).toBeInTheDocument();
    });

    it('should display status information', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Backend API"
        />
      );

      expect(screen.getByText('Backend API')).toBeInTheDocument();
      expect(screen.getByText('Healthy')).toBeInTheDocument();
      expect(screen.getByText('500ms')).toBeInTheDocument();
    });

    it('should format response times correctly', () => {
      const fastStatus = { ...mockHealthyStatus, responseTime: 250 };
      const { rerender } = render(
        <ConnectionStatusIndicator
          status={fastStatus}
          title="Test"
        />
      );

      expect(screen.getByText('250ms')).toBeInTheDocument();

      const slowStatus = { ...mockHealthyStatus, responseTime: 2500 };
      rerender(
        <ConnectionStatusIndicator
          status={slowStatus}
          title="Test"
        />
      );

      expect(screen.getByText('2.50s')).toBeInTheDocument();
    });

    it('should show details when requested', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Test"
          showDetails={true}
        />
      );

      expect(screen.getByText('Success Rate:')).toBeInTheDocument();
      expect(screen.getByText('Endpoint:')).toBeInTheDocument();
    });

    it('should hide details when not requested', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Test"
          showDetails={false}
        />
      );

      expect(screen.queryByText('Success Rate:')).not.toBeInTheDocument();
      expect(screen.queryByText('Endpoint:')).not.toBeInTheDocument();
    });

    it('should calculate success rate correctly', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Test"
          showDetails={true}
        />
      );

      expect(screen.getByText('98.0%')).toBeInTheDocument();
    });

    it('should handle different status types', () => {
      const degradedStatus = { ...mockHealthyStatus, status: 'degraded' as const };
      const { rerender } = render(
        <ConnectionStatusIndicator
          status={degradedStatus}
          title="Test"
        />
      );

      expect(screen.getByText('Degraded')).toBeInTheDocument();

      const failedStatus = { ...mockHealthyStatus, status: 'failed' as const };
      rerender(
        <ConnectionStatusIndicator
          status={failedStatus}
          title="Test"
        />
      );

      expect(screen.getByText('Failed')).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      const { container } = render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Test"
          className="custom-class"
        />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Types Validation', () => {
    it('should have correct ConnectionStatus interface', () => {
      const status: ConnectionStatus = {
        isConnected: true,
        lastCheck: new Date(),
        responseTime: 1000,
        endpoint: 'test',
        status: 'healthy',
        errorCount: 0,
        successCount: 100
      };

      expect(status.isConnected).toBe(true);
      expect(status.status).toBe('healthy');
      expect(typeof status.responseTime).toBe('number');
    });
  });
});