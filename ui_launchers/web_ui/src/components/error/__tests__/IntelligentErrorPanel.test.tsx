/**
 * Tests for IntelligentErrorPanel Component
 * 
 * Tests error display, user interaction, loading states, and API integration.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */


import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { IntelligentErrorPanel, IntelligentErrorPanelProps } from '../IntelligentErrorPanel';
import { getApiClient } from '@/lib/api-client';

// Mock the API client
vi.mock('@/lib/api-client', () => ({
  getApiClient: vi.fn(),
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
  AlertTriangle: ({ className }: { className?: string }) => <div data-testid="alert-triangle-icon" className={className} />,
  RefreshCw: ({ className }: { className?: string }) => <div data-testid="refresh-icon" className={className} />,
  ExternalLink: ({ className }: { className?: string }) => <div data-testid="external-link-icon" className={className} />,
  Clock: ({ className }: { className?: string }) => <div data-testid="clock-icon" className={className} />,
  CheckCircle: ({ className }: { className?: string }) => <div data-testid="check-circle-icon" className={className} />,
  XCircle: ({ className }: { className?: string }) => <div data-testid="x-circle-icon" className={className} />,
  AlertCircle: ({ className }: { className?: string }) => <div data-testid="alert-circle-icon" className={className} />,
  Info: ({ className }: { className?: string }) => <div data-testid="info-icon" className={className} />,
}));

describe('IntelligentErrorPanel', () => {
  const mockApiClient = {
    post: vi.fn(),
  };

  const mockAnalysisResponse = {
    title: 'OpenAI API Key Missing',
    summary: 'The OpenAI API key is not configured in your environment.',
    category: 'api_key_missing',
    severity: 'high' as const,
    next_steps: [
      'Add OPENAI_API_KEY to your .env file',
      'Get your API key from https://platform.openai.com/api-keys',
      'Restart the application after adding the key'
    ],
    provider_health: {
      name: 'openai',
      status: 'unknown' as const,
      success_rate: 95,
      response_time: 1200,
      last_check: '2024-01-15T10:30:00Z'
    },
    contact_admin: false,
    retry_after: null,
    help_url: 'https://platform.openai.com/docs/quickstart',
    technical_details: 'OPENAI_API_KEY environment variable not set',
    cached: false,
    response_time_ms: 150.5
  };

  const defaultProps: IntelligentErrorPanelProps = {
    error: 'OpenAI API key not found',
    errorType: 'AuthenticationError',
    statusCode: 401,
    providerName: 'openai',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (getApiClient as any).mockReturnValue(mockApiClient);
    mockApiClient.post.mockResolvedValue({ data: mockAnalysisResponse });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Loading State', () => {
    it('should show loading state while analyzing error', async () => {
      // Make API call hang to test loading state
      mockApiClient.post.mockImplementation(() => new Promise(() => {}));

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Analyzing Error...')).toBeInTheDocument();
        expect(screen.getByText('Generating intelligent response and next steps')).toBeInTheDocument();
        expect(screen.getByTestId('refresh-icon')).toHaveClass('animate-spin');
      });
    });

    it('should show skeleton loading elements', async () => {
      mockApiClient.post.mockImplementation(() => new Promise(() => {}));

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        // Check for skeleton elements (they should have specific classes)
        const skeletons = screen.getAllByRole('generic').filter(el => 
          el.className.includes('animate-pulse') || el.className.includes('skeleton')
        );
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Analysis Display', () => {
    it('should display error analysis results correctly', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('OpenAI API Key Missing')).toBeInTheDocument();
        expect(screen.getByText('The OpenAI API key is not configured in your environment.')).toBeInTheDocument();
        expect(screen.getByText('HIGH')).toBeInTheDocument();
      });
    });

    it('should display next steps as numbered list', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Next Steps:')).toBeInTheDocument();
        expect(screen.getByText('Add OPENAI_API_KEY to your .env file')).toBeInTheDocument();
        expect(screen.getByText('Get your API key from https://platform.openai.com/api-keys')).toBeInTheDocument();
        expect(screen.getByText('Restart the application after adding the key')).toBeInTheDocument();
        
        // Check for numbered indicators
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    it('should display provider health information', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('openai Status')).toBeInTheDocument();
        expect(screen.getByText('95% success rate')).toBeInTheDocument();
        expect(screen.getByText('1200ms avg')).toBeInTheDocument();
      });
    });

    it('should show appropriate severity icon and styling', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByTestId('alert-triangle-icon')).toBeInTheDocument();
        // Check for high severity styling (orange color)
        const severityIcon = screen.getByTestId('alert-triangle-icon');
        expect(severityIcon).toHaveClass('text-orange-500');
      });
    });
  });

  describe('User Interactions', () => {
    it('should call onRetry when retry button is clicked', async () => {
      const onRetry = vi.fn();
      render(<IntelligentErrorPanel {...defaultProps} onRetry={onRetry} />);

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /try again/i });
        fireEvent.click(retryButton);
        expect(onRetry).toHaveBeenCalledTimes(1);
      });
    });

    it('should call onDismiss when dismiss button is clicked', async () => {
      const onDismiss = vi.fn();
      render(<IntelligentErrorPanel {...defaultProps} onDismiss={onDismiss} />);

      await waitFor(() => {
        const dismissButton = screen.getByRole('button', { name: '×' });
        fireEvent.click(dismissButton);
        expect(onDismiss).toHaveBeenCalledTimes(1);
      });
    });

    it('should open help URL when help button is clicked', async () => {
      const originalOpen = window.open;
      window.open = vi.fn();

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        const helpButton = screen.getByRole('button', { name: /help/i });
        fireEvent.click(helpButton);
        expect(window.open).toHaveBeenCalledWith('https://platform.openai.com/docs/quickstart', '_blank');
      });

      window.open = originalOpen;
    });

    it('should show/hide technical details when details button is clicked', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        const detailsButton = screen.getByRole('button', { name: /show details/i });
        fireEvent.click(detailsButton);
        
        expect(screen.getByText('Technical Details:')).toBeInTheDocument();
        expect(screen.getByText('OPENAI_API_KEY environment variable not set')).toBeInTheDocument();
        
        // Button text should change
        expect(screen.getByRole('button', { name: /hide details/i })).toBeInTheDocument();
      });
    });

    it('should refresh analysis when refresh button is clicked', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        const refreshButton = screen.getByRole('button', { title: 'Refresh analysis' });
        fireEvent.click(refreshButton);
        
        // API should be called again
        expect(mockApiClient.post).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error Handling', () => {
    it('should display fallback analysis when API call fails', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Network error'));

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Error Analysis Unavailable')).toBeInTheDocument();
        expect(screen.getByText('Unable to generate intelligent error response at this time.')).toBeInTheDocument();
        expect(screen.getByText('Contact admin')).toBeInTheDocument();
      });
    });

    it('should show error state with retry option when analysis fails', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Service unavailable'));

      render(<IntelligentErrorPanel {...defaultProps} autoFetch={true} />);

      await waitFor(() => {
        expect(screen.getByText('Analysis Failed')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });
    });
  });

  describe('Retry Logic', () => {
    it('should track retry count and disable retry after max attempts', async () => {
      const onRetry = vi.fn();
      render(<IntelligentErrorPanel {...defaultProps} onRetry={onRetry} maxRetries={2} />);

      await waitFor(() => {
        const retryButton = screen.getByRole('button', { name: /try again/i });
        
        // First retry
        fireEvent.click(retryButton);
        expect(screen.getByRole('button', { name: /try again \(1\/2\)/i })).toBeInTheDocument();
        
        // Second retry
        fireEvent.click(retryButton);
        expect(screen.getByRole('button', { name: /try again \(2\/2\)/i })).toBeInTheDocument();
        
        // Third click should not work (button should be disabled or hidden)
        fireEvent.click(retryButton);
        expect(onRetry).toHaveBeenCalledTimes(2);
      });
    });

    it('should show retry countdown when retry_after is specified', async () => {
      const responseWithRetryAfter = {
        ...mockAnalysisResponse,
        retry_after: 60
      };
      mockApiClient.post.mockResolvedValue({ data: responseWithRetryAfter });

      render(<IntelligentErrorPanel {...defaultProps} onRetry={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Retry in 60s')).toBeInTheDocument();
        expect(screen.getByTestId('clock-icon')).toBeInTheDocument();
      });
    });
  });

  describe('Caching Indicators', () => {
    it('should show cached indicator when response is cached', async () => {
      const cachedResponse = {
        ...mockAnalysisResponse,
        cached: true
      };
      mockApiClient.post.mockResolvedValue({ data: cachedResponse });

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Cached')).toBeInTheDocument();
        expect(screen.getByTestId('clock-icon')).toBeInTheDocument();
      });
    });

    it('should display analysis metadata', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Analysis: 150.5ms')).toBeInTheDocument();
        expect(screen.getByText('Category: api_key_missing')).toBeInTheDocument();
      });
    });
  });

  describe('Contact Admin Functionality', () => {
    it('should show contact admin button when contact_admin is true', async () => {
      const responseWithContactAdmin = {
        ...mockAnalysisResponse,
        contact_admin: true
      };
      mockApiClient.post.mockResolvedValue({ data: responseWithContactAdmin });

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /contact admin/i })).toBeInTheDocument();
      });
    });

    it('should open mailto link when contact admin is clicked', async () => {
      const originalOpen = window.open;
      window.open = vi.fn();

      const responseWithContactAdmin = {
        ...mockAnalysisResponse,
        contact_admin: true
      };
      mockApiClient.post.mockResolvedValue({ data: responseWithContactAdmin });

      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        const contactButton = screen.getByRole('button', { name: /contact admin/i });
        fireEvent.click(contactButton);
        
        expect(window.open).toHaveBeenCalledWith(
          expect.stringContaining('mailto:admin@example.com'),
          '_blank'
        );
      });

      window.open = originalOpen;
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', async () => {
      render(<IntelligentErrorPanel {...defaultProps} />);

      await waitFor(() => {
        // Card should have proper structure
        expect(screen.getByTestId('card')).toBeInTheDocument();
        expect(screen.getByTestId('card-header')).toBeInTheDocument();
        expect(screen.getByTestId('card-content')).toBeInTheDocument();
      });
    });

    it('should have accessible button labels', async () => {
      render(<IntelligentErrorPanel {...defaultProps} onRetry={vi.fn()} onDismiss={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: '×' })).toBeInTheDocument();
        expect(screen.getByRole('button', { title: 'Refresh analysis' })).toBeInTheDocument();
      });
    });
  });

  describe('Props Configuration', () => {
    it('should not auto-fetch when autoFetch is false', () => {
      render(<IntelligentErrorPanel {...defaultProps} autoFetch={false} />);
      
      // API should not be called automatically
      expect(mockApiClient.post).not.toHaveBeenCalled();
    });

    it('should show technical details by default when showTechnicalDetails is true', async () => {
      render(<IntelligentErrorPanel {...defaultProps} showTechnicalDetails={true} />);

      await waitFor(() => {
        expect(screen.getByText('Technical Details:')).toBeInTheDocument();
        expect(screen.getByText('OPENAI_API_KEY environment variable not set')).toBeInTheDocument();
      });
    });

    it('should pass user context to API request', async () => {
      const userContext = { userId: '123', feature: 'chat' };
      render(<IntelligentErrorPanel {...defaultProps} userContext={userContext} />);

      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/api/error-response/analyze',
          expect.objectContaining({
            user_context: expect.objectContaining(userContext)
          })
        );
      });
    });
  });
});