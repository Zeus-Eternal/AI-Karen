/**
 * Tests for ConnectionStatusIndicator component
 */


import { render, screen } from '@testing-library/react';
import { ConnectionStatusIndicator } from '../ConnectionStatusIndicator';
import { ConnectionStatus } from '../types';

describe('ConnectionStatusIndicator', () => {
  const mockHealthyStatus: ConnectionStatus = {
    isConnected: true,
    lastCheck: new Date('2024-01-01T12:00:00Z'),
    responseTime: 500,
    endpoint: 'https://api.example.com',
    status: 'healthy',
    errorCount: 2,
    successCount: 98
  };

  const mockDegradedStatus: ConnectionStatus = {
    isConnected: true,
    lastCheck: new Date('2024-01-01T12:00:00Z'),
    responseTime: 3000,
    endpoint: 'https://api.example.com',
    status: 'degraded',
    errorCount: 15,
    successCount: 85
  };

  const mockFailedStatus: ConnectionStatus = {
    isConnected: false,
    lastCheck: new Date('2024-01-01T11:30:00Z'),
    responseTime: 10000,
    endpoint: 'https://api.example.com',
    status: 'failed',
    errorCount: 50,
    successCount: 50
  };

  beforeEach(() => {
    // Mock current time for consistent testing
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-01-01T12:05:00Z'));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Basic Rendering', () => {
    it('should render healthy status correctly', () => {
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

    it('should render degraded status correctly', () => {
      render(
        <ConnectionStatusIndicator
          status={mockDegradedStatus}
          title="Database"
        />
      );

      expect(screen.getByText('Database')).toBeInTheDocument();
      expect(screen.getByText('Degraded')).toBeInTheDocument();
      expect(screen.getByText('3.00s')).toBeInTheDocument();
    });

    it('should render failed status correctly', () => {
      render(
        <ConnectionStatusIndicator
          status={mockFailedStatus}
          title="Authentication"
        />
      );

      expect(screen.getByText('Authentication')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
      expect(screen.getByText('10.00s')).toBeInTheDocument();
    });
  });

  describe('Response Time Formatting', () => {
    it('should format milliseconds correctly', () => {
      const status = { ...mockHealthyStatus, responseTime: 250 };
      render(
        <ConnectionStatusIndicator
          status={status}
          title="Test"
        />
      );

      expect(screen.getByText('250ms')).toBeInTheDocument();
    });

    it('should format seconds correctly', () => {
      const status = { ...mockHealthyStatus, responseTime: 2500 };
      render(
        <ConnectionStatusIndicator
          status={status}
          title="Test"
        />
      );

      expect(screen.getByText('2.50s')).toBeInTheDocument();
    });
  });

  describe('Last Check Time Formatting', () => {
    it('should show "Just now" for recent checks', () => {
      const status = { ...mockHealthyStatus, lastCheck: new Date('2024-01-01T12:04:30Z') };
      render(
        <ConnectionStatusIndicator
          status={status}
          title="Test"
        />
      );

      expect(screen.getByText('Just now')).toBeInTheDocument();
    });

    it('should show minutes ago for checks within an hour', () => {
      const status = { ...mockHealthyStatus, lastCheck: new Date('2024-01-01T11:58:00Z') };
      render(
        <ConnectionStatusIndicator
          status={status}
          title="Test"
        />
      );

      expect(screen.getByText('7m ago')).toBeInTheDocument();
    });

    it('should show hours ago for older checks', () => {
      const status = { ...mockHealthyStatus, lastCheck: new Date('2024-01-01T10:00:00Z') };
      render(
        <ConnectionStatusIndicator
          status={status}
          title="Test"
        />
      );

      expect(screen.getByText('2h ago')).toBeInTheDocument();
    });
  });

  describe('Success Rate Calculation', () => {
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

    it('should handle zero attempts', () => {
      const status = { ...mockHealthyStatus, successCount: 0, errorCount: 0 };
      render(
        <ConnectionStatusIndicator
          status={status}
          title="Test"
          showDetails={true}
        />
      );

      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });
  });

  describe('Details Display', () => {
    it('should show details when showDetails is true', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Test"
          showDetails={true}
        />
      );

      expect(screen.getByText('Success Rate:')).toBeInTheDocument();
      expect(screen.getByText('Endpoint:')).toBeInTheDocument();
      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(screen.getByText('Errors')).toBeInTheDocument();
      expect(screen.getByText('98')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should hide details when showDetails is false', () => {
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
  });

  describe('Status Colors', () => {
    it('should apply correct colors for response times', () => {
      const { rerender } = render(
        <ConnectionStatusIndicator
          status={{ ...mockHealthyStatus, responseTime: 500 }}
          title="Test"
        />
      );

      // Fast response time should be green
      expect(screen.getByText('500ms')).toHaveClass('text-green-600');

      rerender(
        <ConnectionStatusIndicator
          status={{ ...mockHealthyStatus, responseTime: 3000 }}
          title="Test"
        />
      );

      // Medium response time should be yellow
      expect(screen.getByText('3.00s')).toHaveClass('text-yellow-600');

      rerender(
        <ConnectionStatusIndicator
          status={{ ...mockHealthyStatus, responseTime: 6000 }}
          title="Test"
        />
      );

      // Slow response time should be red
      expect(screen.getByText('6.00s')).toHaveClass('text-red-600');
    });

    it('should apply correct colors for success rates', () => {
      const { rerender } = render(
        <ConnectionStatusIndicator
          status={{ ...mockHealthyStatus, successCount: 98, errorCount: 2 }}
          title="Test"
          showDetails={true}
        />
      );

      // High success rate should be green
      expect(screen.getByText('98.0%')).toHaveClass('text-green-600');

      rerender(
        <ConnectionStatusIndicator
          status={{ ...mockHealthyStatus, successCount: 85, errorCount: 15 }}
          title="Test"
          showDetails={true}
        />
      );

      // Medium success rate should be yellow
      expect(screen.getByText('85.0%')).toHaveClass('text-yellow-600');

      rerender(
        <ConnectionStatusIndicator
          status={{ ...mockHealthyStatus, successCount: 70, errorCount: 30 }}
          title="Test"
          showDetails={true}
        />
      );

      // Low success rate should be red
      expect(screen.getByText('70.0%')).toHaveClass('text-red-600');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and titles', () => {
      render(
        <ConnectionStatusIndicator
          status={mockHealthyStatus}
          title="Backend API"
        />
      );

      const statusIndicator = screen.getByTitle('Status: Healthy');
      expect(statusIndicator).toBeInTheDocument();
    });

    it('should truncate long endpoints with title attribute', () => {
      const longEndpointStatus = {
        ...mockHealthyStatus,
        endpoint: 'https://very-long-api-endpoint-url.example.com/api/v1/health/check'
      };

      render(
        <ConnectionStatusIndicator
          status={longEndpointStatus}
          title="Test"
          showDetails={true}
        />
      );

      const endpointElement = screen.getByTitle(longEndpointStatus.endpoint);
      expect(endpointElement).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
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
});