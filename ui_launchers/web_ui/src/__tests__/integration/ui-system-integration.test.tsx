import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/providers/theme-provider';
import { PreferencesProvider } from '@/providers/preferences-provider';
import { MotionProvider } from '@/providers/motion-provider';
import { AccessibilityProvider } from '@/providers/accessibility-provider';
import { useUIStore } from '@/store/ui-store';
import { GridContainer } from '@/components/ui/layout/grid-container';
import { FlexContainer } from '@/components/ui/layout/flex-container';
import { ResponsiveContainer } from '@/components/ui/layout/responsive-container';
import { InteractiveButton } from '@/components/ui/micro-interactions/interactive-button';
import { InteractiveInput } from '@/components/ui/micro-interactions/interactive-input';
import { Card } from '@/components/ui/compound/card';
import { Modal } from '@/components/ui/compound/modal';
import { Form } from '@/components/ui/compound/form';
import { RightPanel } from '@/components/ui/right-panel';
import { ModernErrorBoundary } from '@/components/error/modern-error-boundary';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
    button: React.forwardRef<HTMLButtonElement, any>(({ children, ...props }, ref) => (
      <button ref={ref} {...props}>{children}</button>
    )),
    input: React.forwardRef<HTMLInputElement, any>((props, ref) => (
      <input ref={ref} {...props} />
    )),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAnimation: () => ({
    start: vi.fn(),
    stop: vi.fn(),
    set: vi.fn(),
  }),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Test wrapper with all providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <PreferencesProvider>
          <MotionProvider>
            <AccessibilityProvider>
              <ModernErrorBoundary>
                {children}
              </ModernErrorBoundary>
            </AccessibilityProvider>
          </MotionProvider>
        </PreferencesProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('UI System Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useUIStore.getState().reset?.();
  });

  describe('Complete User Workflows', () => {
    it('should handle complete form submission workflow', async () => {
      const onSubmit = vi.fn();
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <ResponsiveContainer>
            <Card.Root>
              <Card.Header>
                <Card.Title>Contact Form</Card.Title>
              </Card.Header>
              <Card.Content>
                <Form.Root onSubmit={onSubmit}>
                  <Form.Field>
                    <Form.Label htmlFor="name">Name</Form.Label>
                    <InteractiveInput
                      id="name"
                      name="name"
                      required
                      data-testid="name-input"
                    />
                  </Form.Field>
                  <Form.Field>
                    <Form.Label htmlFor="email">Email</Form.Label>
                    <InteractiveInput
                      id="email"
                      name="email"
                      type="email"
                      required
                      data-testid="email-input"
                    />
                  </Form.Field>
                  <Form.Actions>
                    <InteractiveButton type="submit" data-testid="submit-btn">
                      Submit
                    </InteractiveButton>
                  </Form.Actions>
                </Form.Root>
              </Card.Content>
            </Card.Root>
          </ResponsiveContainer>
        </TestWrapper>
      );

      // Fill out form
      const nameInput = screen.getByTestId('name-input');
      const emailInput = screen.getByTestId('email-input');
      const submitButton = screen.getByTestId('submit-btn');

      await user.type(nameInput, 'John Doe');
      await user.type(emailInput, 'john@example.com');

      // Submit form
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'John Doe',
            email: 'john@example.com',
          })
        );
      });
    });

    it('should handle modal workflow with focus management', async () => {
      const user = userEvent.setup();

      const ModalWorkflow = () => {
        const [isOpen, setIsOpen] = React.useState(false);

        return (
          <TestWrapper>
            <div>
              <InteractiveButton
                onClick={() => setIsOpen(true)}
                data-testid="open-modal"
              >
                Open Modal
              </InteractiveButton>
              
              <Modal.Root open={isOpen} onOpenChange={setIsOpen}>
                <Modal.Content data-testid="modal-content">
                  <Modal.Header>
                    <Modal.Title>Confirm Action</Modal.Title>
                  </Modal.Header>
                  <Modal.Body>
                    <p>Are you sure you want to continue?</p>
                  </Modal.Body>
                  <Modal.Actions>
                    <InteractiveButton
                      variant="secondary"
                      onClick={() => setIsOpen(false)}
                      data-testid="cancel-btn"
                    >
                      Cancel
                    </InteractiveButton>
                    <InteractiveButton
                      variant="primary"
                      onClick={() => setIsOpen(false)}
                      data-testid="confirm-btn"
                    >
                      Confirm
                    </InteractiveButton>
                  </Modal.Actions>
                </Modal.Content>
              </Modal.Root>
            </div>
          </TestWrapper>
        );
      };

      render(<ModalWorkflow />);

      const openButton = screen.getByTestId('open-modal');
      
      // Open modal
      await user.click(openButton);

      const modal = screen.getByTestId('modal-content');
      expect(modal).toBeInTheDocument();

      // Focus should be trapped in modal
      const cancelButton = screen.getByTestId('cancel-btn');
      const confirmButton = screen.getByTestId('confirm-btn');

      expect(cancelButton).toBeInTheDocument();
      expect(confirmButton).toBeInTheDocument();

      // Close modal
      await user.click(cancelButton);

      await waitFor(() => {
        expect(modal).not.toBeInTheDocument();
      });

      // Focus should return to trigger
      expect(openButton).toHaveFocus();
    });

    it('should handle responsive layout changes', async () => {
      const user = userEvent.setup();

      // Mock different viewport sizes
      const mockMatchMedia = (query: string) => ({
        matches: query.includes('768px'), // Mock medium screen
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      });

      window.matchMedia = vi.fn().mockImplementation(mockMatchMedia);

      render(
        <TestWrapper>
          <ResponsiveContainer responsive>
            <GridContainer
              columns={{ base: 1, md: 2, lg: 3 }}
              gap="1rem"
              responsive
              data-testid="responsive-grid"
            >
              <Card.Root data-testid="card-1">
                <Card.Content>Card 1</Card.Content>
              </Card.Root>
              <Card.Root data-testid="card-2">
                <Card.Content>Card 2</Card.Content>
              </Card.Root>
              <Card.Root data-testid="card-3">
                <Card.Content>Card 3</Card.Content>
              </Card.Root>
            </GridContainer>
          </ResponsiveContainer>
        </TestWrapper>
      );

      const grid = screen.getByTestId('responsive-grid');
      expect(grid).toHaveClass('responsive-grid');

      const cards = [
        screen.getByTestId('card-1'),
        screen.getByTestId('card-2'),
        screen.getByTestId('card-3'),
      ];

      cards.forEach(card => {
        expect(card).toBeInTheDocument();
      });
    });
  });

  describe('State Management Integration', () => {
    it('should integrate with UI store for theme changes', async () => {
      const user = userEvent.setup();

      const ThemeToggle = () => {
        const { theme, setTheme } = useUIStore();

        return (
          <TestWrapper>
            <div data-testid="current-theme">{theme}</div>
            <InteractiveButton
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              data-testid="theme-toggle"
            >
              Toggle Theme
            </InteractiveButton>
          </TestWrapper>
        );
      };

      render(<ThemeToggle />);

      const themeDisplay = screen.getByTestId('current-theme');
      const toggleButton = screen.getByTestId('theme-toggle');

      // Initial theme
      expect(themeDisplay).toHaveTextContent('system');

      // Toggle theme
      await user.click(toggleButton);
      expect(themeDisplay).toHaveTextContent('light');

      await user.click(toggleButton);
      expect(themeDisplay).toHaveTextContent('dark');
    });

    it('should integrate with UI store for sidebar state', async () => {
      const user = userEvent.setup();

      const SidebarToggle = () => {
        const { sidebarCollapsed, toggleSidebar } = useUIStore();

        return (
          <TestWrapper>
            <div data-testid="sidebar-state">
              {sidebarCollapsed ? 'collapsed' : 'expanded'}
            </div>
            <InteractiveButton
              onClick={toggleSidebar}
              data-testid="sidebar-toggle"
            >
              Toggle Sidebar
            </InteractiveButton>
          </TestWrapper>
        );
      };

      render(<SidebarToggle />);

      const sidebarState = screen.getByTestId('sidebar-state');
      const toggleButton = screen.getByTestId('sidebar-toggle');

      // Initial state
      expect(sidebarState).toHaveTextContent('expanded');

      // Toggle sidebar
      await user.click(toggleButton);
      expect(sidebarState).toHaveTextContent('collapsed');

      await user.click(toggleButton);
      expect(sidebarState).toHaveTextContent('expanded');
    });

    it('should integrate with right panel state management', async () => {
      const user = userEvent.setup();

      const RightPanelDemo = () => {
        const { rightPanelView, setRightPanelView } = useUIStore();

        return (
          <TestWrapper>
            <FlexContainer>
              <div>
                <InteractiveButton
                  onClick={() => setRightPanelView('dashboard')}
                  data-testid="dashboard-btn"
                >
                  Dashboard
                </InteractiveButton>
                <InteractiveButton
                  onClick={() => setRightPanelView('settings')}
                  data-testid="settings-btn"
                >
                  Settings
                </InteractiveButton>
                <InteractiveButton
                  onClick={() => setRightPanelView('analytics')}
                  data-testid="analytics-btn"
                >
                  Analytics
                </InteractiveButton>
              </div>
              <RightPanel
                activeView={rightPanelView}
                onViewChange={setRightPanelView}
                data-testid="right-panel"
              >
                {rightPanelView === 'dashboard' && <div>Dashboard Content</div>}
                {rightPanelView === 'settings' && <div>Settings Content</div>}
                {rightPanelView === 'analytics' && <div>Analytics Content</div>}
              </RightPanel>
            </FlexContainer>
          </TestWrapper>
        );
      };

      render(<RightPanelDemo />);

      const dashboardBtn = screen.getByTestId('dashboard-btn');
      const settingsBtn = screen.getByTestId('settings-btn');
      const analyticsBtn = screen.getByTestId('analytics-btn');

      // Initial state should show dashboard
      expect(screen.getByText('Dashboard Content')).toBeInTheDocument();

      // Switch to settings
      await user.click(settingsBtn);
      await waitFor(() => {
        expect(screen.getByText('Settings Content')).toBeInTheDocument();
      });

      // Switch to analytics
      await user.click(analyticsBtn);
      await waitFor(() => {
        expect(screen.getByText('Analytics Content')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle component errors gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const ErrorComponent = ({ shouldError }: { shouldError: boolean }) => {
        if (shouldError) {
          throw new Error('Test error');
        }
        return <div>Working component</div>;
      };

      const ErrorDemo = () => {
        const [hasError, setHasError] = React.useState(false);

        return (
          <TestWrapper>
            <InteractiveButton
              onClick={() => setHasError(true)}
              data-testid="trigger-error"
            >
              Trigger Error
            </InteractiveButton>
            <ErrorComponent shouldError={hasError} />
          </TestWrapper>
        );
      };

      const user = userEvent.setup();
      render(<ErrorDemo />);

      // Initially working
      expect(screen.getByText('Working component')).toBeInTheDocument();

      // Trigger error
      const errorButton = screen.getByTestId('trigger-error');
      await user.click(errorButton);

      // Should show error boundary
      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });

    it('should handle async errors with retry mechanism', async () => {
      const user = userEvent.setup();
      let attemptCount = 0;

      const AsyncComponent = () => {
        const [data, setData] = React.useState<string | null>(null);
        const [error, setError] = React.useState<string | null>(null);
        const [loading, setLoading] = React.useState(false);

        const fetchData = async () => {
          setLoading(true);
          setError(null);
          attemptCount++;

          try {
            // Simulate API call that fails first time
            if (attemptCount === 1) {
              throw new Error('Network error');
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
            setData('Success data');
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setLoading(false);
          }
        };

        return (
          <TestWrapper>
            <div>
              {loading && <div>Loading...</div>}
              {error && (
                <div>
                  <div>Error: {error}</div>
                  <InteractiveButton
                    onClick={fetchData}
                    data-testid="retry-btn"
                  >
                    Retry
                  </InteractiveButton>
                </div>
              )}
              {data && <div>Data: {data}</div>}
              {!loading && !error && !data && (
                <InteractiveButton
                  onClick={fetchData}
                  data-testid="load-btn"
                >
                  Load Data
                </InteractiveButton>
              )}
            </div>
          </TestWrapper>
        );
      };

      render(<AsyncComponent />);

      // Initial load
      const loadButton = screen.getByTestId('load-btn');
      await user.click(loadButton);

      // Should show loading
      expect(screen.getByText('Loading...')).toBeInTheDocument();

      // Should show error
      await waitFor(() => {
        expect(screen.getByText('Error: Network error')).toBeInTheDocument();
      });

      // Retry should succeed
      const retryButton = screen.getByTestId('retry-btn');
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Data: Success data')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should adapt layout based on container size', async () => {
      // Mock ResizeObserver to simulate container size changes
      const mockObserver = {
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };

      global.ResizeObserver = vi.fn().mockImplementation((callback) => {
        // Simulate size change
        setTimeout(() => {
          callback([{
            contentRect: { width: 800, height: 600 },
            target: document.createElement('div'),
          }]);
        }, 100);
        
        return mockObserver;
      });

      const ResponsiveDemo = () => {
        const [containerSize, setContainerSize] = React.useState('small');

        React.useEffect(() => {
          const timer = setTimeout(() => {
            setContainerSize('large');
          }, 200);

          return () => clearTimeout(timer);
        }, []);

        return (
          <TestWrapper>
            <ResponsiveContainer
              containerQueries
              containerName="demo"
              data-testid="responsive-container"
            >
              <div data-testid="size-indicator">
                Container size: {containerSize}
              </div>
              <GridContainer
                columns={containerSize === 'large' ? 3 : 1}
                gap="1rem"
                data-testid="responsive-grid"
              >
                <div>Item 1</div>
                <div>Item 2</div>
                <div>Item 3</div>
              </GridContainer>
            </ResponsiveContainer>
          </TestWrapper>
        );
      };

      render(<ResponsiveDemo />);

      const container = screen.getByTestId('responsive-container');
      expect(container).toHaveStyle({ containerType: 'inline-size' });

      // Wait for size change
      await waitFor(() => {
        expect(screen.getByText('Container size: large')).toBeInTheDocument();
      });
    });

    it('should handle touch interactions on mobile', async () => {
      // Mock touch events
      const mockTouchEvent = {
        touches: [{ clientX: 100, clientY: 100 }],
        preventDefault: vi.fn(),
      };

      const TouchDemo = () => {
        const [touchCount, setTouchCount] = React.useState(0);

        return (
          <TestWrapper>
            <InteractiveButton
              onTouchStart={() => setTouchCount(c => c + 1)}
              data-testid="touch-button"
            >
              Touch me
            </InteractiveButton>
            <div data-testid="touch-count">Touches: {touchCount}</div>
          </TestWrapper>
        );
      };

      render(<TouchDemo />);

      const button = screen.getByTestId('touch-button');
      const counter = screen.getByTestId('touch-count');

      // Simulate touch
      fireEvent.touchStart(button, mockTouchEvent);

      await waitFor(() => {
        expect(counter).toHaveTextContent('Touches: 1');
      });
    });
  });

  describe('Performance Integration', () => {
    it('should handle large datasets efficiently', async () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        value: Math.random() * 100,
      }));

      const LargeListDemo = () => {
        const [filter, setFilter] = React.useState('');
        
        const filteredData = React.useMemo(() => {
          return largeDataset.filter(item =>
            item.name.toLowerCase().includes(filter.toLowerCase())
          );
        }, [filter]);

        return (
          <TestWrapper>
            <InteractiveInput
              placeholder="Filter items..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              data-testid="filter-input"
            />
            <div data-testid="item-count">
              Showing {filteredData.length} items
            </div>
            <GridContainer
              columns="repeat(auto-fill, minmax(200px, 1fr))"
              gap="1rem"
              data-testid="items-grid"
            >
              {filteredData.slice(0, 50).map(item => (
                <Card.Root key={item.id} data-testid={`item-${item.id}`}>
                  <Card.Content>
                    <div>{item.name}</div>
                    <div>Value: {item.value.toFixed(2)}</div>
                  </Card.Content>
                </Card.Root>
              ))}
            </GridContainer>
          </TestWrapper>
        );
      };

      const user = userEvent.setup();
      render(<LargeListDemo />);

      // Initial render should show all items (limited to 50)
      expect(screen.getByTestId('item-count')).toHaveTextContent('Showing 1000 items');

      // Filter should work efficiently
      const filterInput = screen.getByTestId('filter-input');
      await user.type(filterInput, '100');

      await waitFor(() => {
        expect(screen.getByTestId('item-count')).toHaveTextContent('Showing 1 items');
      });

      // Clear filter
      await user.clear(filterInput);

      await waitFor(() => {
        expect(screen.getByTestId('item-count')).toHaveTextContent('Showing 1000 items');
      });
    });

    it('should optimize re-renders with proper memoization', async () => {
      const renderCount = { parent: 0, child: 0 };

      const ChildComponent = React.memo(({ value }: { value: string }) => {
        renderCount.child++;
        return <div data-testid="child-value">{value}</div>;
      });

      const ParentComponent = () => {
        renderCount.parent++;
        const [parentState, setParentState] = React.useState(0);
        const [childValue] = React.useState('stable value');

        return (
          <TestWrapper>
            <div data-testid="parent-renders">Parent renders: {renderCount.parent}</div>
            <div data-testid="child-renders">Child renders: {renderCount.child}</div>
            <InteractiveButton
              onClick={() => setParentState(s => s + 1)}
              data-testid="update-parent"
            >
              Update Parent ({parentState})
            </InteractiveButton>
            <ChildComponent value={childValue} />
          </TestWrapper>
        );
      };

      const user = userEvent.setup();
      render(<ParentComponent />);

      // Initial render
      expect(screen.getByTestId('parent-renders')).toHaveTextContent('Parent renders: 1');
      expect(screen.getByTestId('child-renders')).toHaveTextContent('Child renders: 1');

      // Update parent state
      const updateButton = screen.getByTestId('update-parent');
      await user.click(updateButton);

      await waitFor(() => {
        expect(screen.getByTestId('parent-renders')).toHaveTextContent('Parent renders: 2');
        // Child should not re-render due to memoization
        expect(screen.getByTestId('child-renders')).toHaveTextContent('Child renders: 1');
      });
    });
  });
});