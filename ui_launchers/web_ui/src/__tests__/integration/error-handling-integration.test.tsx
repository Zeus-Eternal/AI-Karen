import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ModernErrorBoundary } from '@/components/error/modern-error-boundary';
import { OptimisticErrorBoundary } from '@/components/error/optimistic-error-boundary';
import { SectionErrorBoundaries } from '@/components/error/section-error-boundaries';
import { useErrorRecovery } from '@/hooks/use-error-recovery';
import { useOptimisticUpdates } from '@/hooks/use-optimistic-updates';
import { InteractiveButton } from '@/components/ui/micro-interactions/interactive-button';
import { InteractiveInput } from '@/components/ui/micro-interactions/interactive-input';
import { Card } from '@/components/ui/compound/card';
import { Form } from '@/components/ui/compound/form';
import { GridContainer } from '@/components/ui/layout/grid-container';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
    button: React.forwardRef<HTMLButtonElement, any>(({ children, ...props }, ref) => (
      <button ref={ref} {...props}>{children}</button>
    )),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock console methods to avoid noise in tests
const mockConsole = {
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
  warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
  log: vi.spyOn(console, 'log').mockImplementation(() => {}),
};

// Test wrapper with query client
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Error Handling Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockConsole.error.mockClear();
    mockConsole.warn.mockClear();
    mockConsole.log.mockClear();

  afterEach(() => {
    mockConsole.error.mockRestore();
    mockConsole.warn.mockRestore();
    mockConsole.log.mockRestore();

  describe('Error Boundary Integration', () => {
    it('should handle component errors with retry functionality', async () => {
      const user = userEvent.setup();
      let shouldError = true;

      const ErrorProneComponent = () => {
        if (shouldError) {
          throw new Error('Component error');
        }
        return <div data-testid="success-content">Component loaded successfully</div>;
      };

      const ErrorDemo = () => {
        const [key, setKey] = React.useState(0);

        return (
          <TestWrapper>
            <ModernErrorBoundary
              onRetry={() => {
                shouldError = false;
                setKey(k => k + 1);
              }}
              maxRetries={3}
            >
              <ErrorProneComponent key={key} />
            </ModernErrorBoundary>
          </TestWrapper>
        );
      };

      render(<ErrorDemo />);

      // Should show error boundary
      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      // Should have retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();

      // Retry should work
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByTestId('success-content')).toBeInTheDocument();


    it('should handle section-specific errors without affecting other sections', async () => {
      const user = userEvent.setup();
      let headerError = false;
      let contentError = false;

      const HeaderComponent = () => {
        if (headerError) {
          throw new Error('Header error');
        }
        return <div data-testid="header-content">Header Content</div>;
      };

      const ContentComponent = () => {
        if (contentError) {
          throw new Error('Content error');
        }
        return <div data-testid="main-content">Main Content</div>;
      };

      const SectionErrorDemo = () => {
        return (
          <TestWrapper>
            <GridContainer columns="1fr" rows="auto 1fr" gap="1rem">
              <SectionErrorBoundaries.Header>
                <HeaderComponent />
              </SectionErrorBoundaries.Header>
              
              <SectionErrorBoundaries.Content>
                <ContentComponent />
              </SectionErrorBoundaries.Content>
              
              <div>
                <InteractiveButton
                  onClick={() => { headerError = true; }}
                  data-testid="trigger-header-error"
                >
                </InteractiveButton>
                <InteractiveButton
                  onClick={() => { contentError = true; }}
                  data-testid="trigger-content-error"
                >
                </InteractiveButton>
              </div>
            </GridContainer>
          </TestWrapper>
        );
      };

      render(<SectionErrorDemo />);

      // Initially both sections should work
      expect(screen.getByTestId('header-content')).toBeInTheDocument();
      expect(screen.getByTestId('main-content')).toBeInTheDocument();

      // Break header
      const headerErrorButton = screen.getByTestId('trigger-header-error');
      await user.click(headerErrorButton);

      await waitFor(() => {
        // Header should show error
        expect(screen.queryByTestId('header-content')).not.toBeInTheDocument();
        // Content should still work
        expect(screen.getByTestId('main-content')).toBeInTheDocument();


    it('should handle optimistic updates with error recovery', async () => {
      const user = userEvent.setup();
      let shouldFail = false;

      const OptimisticDemo = () => {
        const [items, setItems] = React.useState(['Item 1', 'Item 2']);
        const [isLoading, setIsLoading] = React.useState(false);

        const { executeOptimistically } = useOptimisticUpdates();

        const addItem = async (newItem: string) => {
          setIsLoading(true);
          
          try {
            await executeOptimistically(
              // Optimistic update
              () => setItems(prev => [...prev, newItem]),
              // Actual operation
              async () => {
                await new Promise(resolve => setTimeout(resolve, 100));
                if (shouldFail) {
                  throw new Error('Server error');
                }
                return newItem;
              },
              // Rollback on error
              () => setItems(prev => prev.slice(0, -1))
            );
          } catch (error) {
            // Error is handled by the hook
          } finally {
            setIsLoading(false);
          }
        };

        return (
          <TestWrapper>
            <OptimisticErrorBoundary>
              <div>
                <div data-testid="items-list">
                  {items.map((item, index) => (
                    <div key={index} data-testid={`item-${index}`}>
                      {item}
                    </div>
                  ))}
                </div>
                
                <div>
                  <InteractiveButton
                    onClick={() => addItem('New Item')}
                    disabled={isLoading}
                    data-testid="add-item"
                  >
                    {isLoading ? 'Adding...' : 'Add Item'}
                  </InteractiveButton>
                  
                  <InteractiveButton
                    onClick={() => { shouldFail = !shouldFail; }}
                    data-testid="toggle-failure"
                  >
                    {shouldFail ? 'Disable Failure' : 'Enable Failure'}
                  </InteractiveButton>
                </div>
              </div>
            </OptimisticErrorBoundary>
          </TestWrapper>
        );
      };

      render(<OptimisticDemo />);

      // Initially should have 2 items
      expect(screen.getByTestId('item-0')).toHaveTextContent('Item 1');
      expect(screen.getByTestId('item-1')).toHaveTextContent('Item 2');

      // Add item successfully
      const addButton = screen.getByTestId('add-item');
      await user.click(addButton);

      // Should immediately show optimistic update
      expect(screen.getByTestId('item-2')).toHaveTextContent('New Item');

      await waitFor(() => {
        expect(screen.getByTestId('add-item')).not.toBeDisabled();

      // Enable failure and try again
      const toggleFailure = screen.getByTestId('toggle-failure');
      await user.click(toggleFailure);

      await user.click(addButton);

      // Should show optimistic update first
      await waitFor(() => {
        expect(screen.getByTestId('item-3')).toBeInTheDocument();

      // Then should rollback on error
      await waitFor(() => {
        expect(screen.queryByTestId('item-3')).not.toBeInTheDocument();



  describe('Form Error Handling', () => {
    it('should handle form validation errors gracefully', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();

      const FormErrorDemo = () => {
        const [errors, setErrors] = React.useState<Record<string, string>>({});

        const handleSubmit = async (data: Record<string, string>) => {
          const newErrors: Record<string, string> = {};

          if (!data.email) {
            newErrors.email = 'Email is required';
          } else if (!data.email.includes('@')) {
            newErrors.email = 'Invalid email format';
          }

          if (!data.password) {
            newErrors.password = 'Password is required';
          } else if (data.password.length < 8) {
            newErrors.password = 'Password must be at least 8 characters';
          }

          setErrors(newErrors);

          if (Object.keys(newErrors).length === 0) {
            onSubmit(data);
          }
        };

        return (
          <TestWrapper>
            <ModernErrorBoundary>
              <Card.Root>
                <Card.Header>
                  <Card.Title>Login Form</Card.Title>
                </Card.Header>
                <Card.Content>
                  <Form.Root onSubmit={handleSubmit}>
                    <Form.Field>
                      <Form.Label htmlFor="email">Email</Form.Label>
                      <InteractiveInput
                        id="email"
                        name="email"
                        type="email"
                        error={errors.email}
                        data-testid="email-input"
                      />
                      {errors.email && (
                        <Form.Error data-testid="email-error">
                          {errors.email}
                        </Form.Error>
                      )}
                    </Form.Field>

                    <Form.Field>
                      <Form.Label htmlFor="password">Password</Form.Label>
                      <InteractiveInput
                        id="password"
                        name="password"
                        type="password"
                        error={errors.password}
                        data-testid="password-input"
                      />
                      {errors.password && (
                        <Form.Error data-testid="password-error">
                          {errors.password}
                        </Form.Error>
                      )}
                    </Form.Field>

                    <Form.Actions>
                      <InteractiveButton type="submit" data-testid="submit-btn">
                      </InteractiveButton>
                    </Form.Actions>
                  </Form.Root>
                </Card.Content>
              </Card.Root>
            </ModernErrorBoundary>
          </TestWrapper>
        );
      };

      render(<FormErrorDemo />);

      const emailInput = screen.getByTestId('email-input');
      const passwordInput = screen.getByTestId('password-input');
      const submitButton = screen.getByTestId('submit-btn');

      // Submit empty form
      await user.click(submitButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByTestId('email-error')).toHaveTextContent('Email is required');
        expect(screen.getByTestId('password-error')).toHaveTextContent('Password is required');

      // Fix email, keep password invalid
      await user.type(emailInput, 'invalid-email');
      await user.type(passwordInput, '123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByTestId('email-error')).toHaveTextContent('Invalid email format');
        expect(screen.getByTestId('password-error')).toHaveTextContent('Password must be at least 8 characters');

      // Fix both fields
      await user.clear(emailInput);
      await user.type(emailInput, 'user@example.com');
      await user.clear(passwordInput);
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Should submit successfully
      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          email: 'user@example.com',
          password: 'password123',


      // Errors should be cleared
      expect(screen.queryByTestId('email-error')).not.toBeInTheDocument();
      expect(screen.queryByTestId('password-error')).not.toBeInTheDocument();


  describe('Network Error Recovery', () => {
    it('should handle network errors with exponential backoff', async () => {
      const user = userEvent.setup();
      let attemptCount = 0;
      const maxAttempts = 3;

      const NetworkErrorDemo = () => {
        const [status, setStatus] = React.useState<'idle' | 'loading' | 'success' | 'error'>('idle');
        const [data, setData] = React.useState<string | null>(null);

        const { retry } = useErrorRecovery({
          maxRetries: maxAttempts,
          baseDelay: 100,
          maxDelay: 1000,

        const fetchData = async () => {
          setStatus('loading');
          setData(null);

          try {
            await retry(async () => {
              attemptCount++;
              
              // Simulate network failure for first 2 attempts
              if (attemptCount < 3) {
                throw new Error(`Network error (attempt ${attemptCount})`);
              }
              
              // Success on 3rd attempt
              await new Promise(resolve => setTimeout(resolve, 50));
              return 'Success data';

            setData('Success data');
            setStatus('success');
          } catch (error) {
            setStatus('error');
          }
        };

        return (
          <TestWrapper>
            <ModernErrorBoundary>
              <div>
                <div data-testid="status">Status: {status}</div>
                <div data-testid="attempt-count">Attempts: {attemptCount}</div>
                {data && <div data-testid="data">Data: {data}</div>}
                
                <InteractiveButton
                  onClick={fetchData}
                  disabled={status === 'loading'}
                  data-testid="fetch-btn"
                >
                  {status === 'loading' ? 'Loading...' : 'Fetch Data'}
                </InteractiveButton>
                
                {status === 'error' && (
                  <InteractiveButton
                    onClick={() => {
                      attemptCount = 0;
                      fetchData();
                    }}
                    data-testid="reset-btn"
                  >
                  </InteractiveButton>
                )}
              </div>
            </ModernErrorBoundary>
          </TestWrapper>
        );
      };

      render(<NetworkErrorDemo />);

      const fetchButton = screen.getByTestId('fetch-btn');
      const statusDisplay = screen.getByTestId('status');
      const attemptDisplay = screen.getByTestId('attempt-count');

      // Initial state
      expect(statusDisplay).toHaveTextContent('Status: idle');
      expect(attemptDisplay).toHaveTextContent('Attempts: 0');

      // Start fetch
      await user.click(fetchButton);

      // Should show loading
      expect(statusDisplay).toHaveTextContent('Status: loading');

      // Should eventually succeed after retries
      await waitFor(() => {
        expect(statusDisplay).toHaveTextContent('Status: success');
        expect(attemptDisplay).toHaveTextContent('Attempts: 3');
        expect(screen.getByTestId('data')).toHaveTextContent('Data: Success data');
      }, { timeout: 5000 });

    it('should handle offline/online state changes', async () => {
      const user = userEvent.setup();

      const OfflineDemo = () => {
        const [isOnline, setIsOnline] = React.useState(navigator.onLine);
        const [queuedActions, setQueuedActions] = React.useState<string[]>([]);

        React.useEffect(() => {
          const handleOnline = () => setIsOnline(true);
          const handleOffline = () => setIsOnline(false);

          window.addEventListener('online', handleOnline);
          window.addEventListener('offline', handleOffline);

          return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
          };
        }, []);

        const performAction = (action: string) => {
          if (isOnline) {
            // Perform action immediately
            console.log(`Performing: ${action}`);
          } else {
            // Queue for later
            setQueuedActions(prev => [...prev, action]);
          }
        };

        const processQueue = () => {
          queuedActions.forEach(action => {
            console.log(`Processing queued: ${action}`);

          setQueuedActions([]);
        };

        React.useEffect(() => {
          if (isOnline && queuedActions.length > 0) {
            processQueue();
          }
        }, [isOnline]);

        return (
          <TestWrapper>
            <ModernErrorBoundary>
              <div>
                <div data-testid="online-status">
                  Status: {isOnline ? 'Online' : 'Offline'}
                </div>
                <div data-testid="queue-count">
                  Queued actions: {queuedActions.length}
                </div>
                
                <InteractiveButton
                  onClick={() => performAction('Save document')}
                  data-testid="save-btn"
                >
                </InteractiveButton>
                
                <InteractiveButton
                  onClick={() => setIsOnline(!isOnline)}
                  data-testid="toggle-online"
                >
                  {isOnline ? 'Go Offline' : 'Go Online'}
                </InteractiveButton>
              </div>
            </ModernErrorBoundary>
          </TestWrapper>
        );
      };

      render(<OfflineDemo />);

      const statusDisplay = screen.getByTestId('online-status');
      const queueDisplay = screen.getByTestId('queue-count');
      const saveButton = screen.getByTestId('save-btn');
      const toggleButton = screen.getByTestId('toggle-online');

      // Initially online
      expect(statusDisplay).toHaveTextContent('Status: Online');
      expect(queueDisplay).toHaveTextContent('Queued actions: 0');

      // Go offline
      await user.click(toggleButton);
      expect(statusDisplay).toHaveTextContent('Status: Offline');

      // Perform actions while offline
      await user.click(saveButton);
      await user.click(saveButton);

      expect(queueDisplay).toHaveTextContent('Queued actions: 2');

      // Go back online
      await user.click(toggleButton);
      expect(statusDisplay).toHaveTextContent('Status: Online');

      // Queue should be processed
      await waitFor(() => {
        expect(queueDisplay).toHaveTextContent('Queued actions: 0');



  describe('Graceful Degradation', () => {
    it('should degrade gracefully when features are unavailable', async () => {
      // Mock missing APIs
      const originalIntersectionObserver = global.IntersectionObserver;
      const originalResizeObserver = global.ResizeObserver;

      // @ts-expect-error - Testing missing API
      global.IntersectionObserver = undefined;
      // @ts-expect-error - Testing missing API
      global.ResizeObserver = undefined;

      const GracefulDemo = () => {
        const [hasIntersectionObserver] = React.useState(
          typeof IntersectionObserver !== 'undefined'
        );
        const [hasResizeObserver] = React.useState(
          typeof ResizeObserver !== 'undefined'
        );

        return (
          <TestWrapper>
            <ModernErrorBoundary>
              <div>
                <div data-testid="intersection-support">
                  Intersection Observer: {hasIntersectionObserver ? 'Supported' : 'Not supported'}
                </div>
                <div data-testid="resize-support">
                  Resize Observer: {hasResizeObserver ? 'Supported' : 'Not supported'}
                </div>
                
                {/* Component should still work without these APIs */}
                <GridContainer columns={3} gap="1rem" data-testid="fallback-grid">
                  <Card.Root>
                    <Card.Content>Card 1</Card.Content>
                  </Card.Root>
                  <Card.Root>
                    <Card.Content>Card 2</Card.Content>
                  </Card.Root>
                  <Card.Root>
                    <Card.Content>Card 3</Card.Content>
                  </Card.Root>
                </GridContainer>
              </div>
            </ModernErrorBoundary>
          </TestWrapper>
        );
      };

      render(<GracefulDemo />);

      // Should show that APIs are not supported
      expect(screen.getByTestId('intersection-support')).toHaveTextContent('Not supported');
      expect(screen.getByTestId('resize-support')).toHaveTextContent('Not supported');

      // But components should still render
      expect(screen.getByTestId('fallback-grid')).toBeInTheDocument();
      expect(screen.getByText('Card 1')).toBeInTheDocument();
      expect(screen.getByText('Card 2')).toBeInTheDocument();
      expect(screen.getByText('Card 3')).toBeInTheDocument();

      // Restore APIs
      global.IntersectionObserver = originalIntersectionObserver;
      global.ResizeObserver = originalResizeObserver;


