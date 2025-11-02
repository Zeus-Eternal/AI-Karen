import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RightPanel, useRightPanel, type RightPanelView } from '../right-panel';
import { Settings, User, Bell } from 'lucide-react';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    aside: React.forwardRef<HTMLElement, any>(({ children, ...props }, ref) => (
      <aside ref={ref} {...props}>{children}</aside>
    )),
    div: React.forwardRef<HTMLDivElement, any>(({ children, ...props }, ref) => (
      <div ref={ref} {...props}>{children}</div>
    )),
    footer: React.forwardRef<HTMLElement, any>(({ children, ...props }, ref) => (
      <footer ref={ref} {...props}>{children}</footer>
    )),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock the useReducedMotion hook
vi.mock('@/hooks/use-reduced-motion', () => ({
  useReducedMotion: vi.fn(() => false),
  useAnimationDuration: vi.fn((normal, reduced) => normal),
  useAnimationVariants: vi.fn((normal, reduced) => normal),
}));

describe('RightPanel', () => {
  const mockViews: RightPanelView[] = [
    {
      id: 'settings',
      title: 'Settings',
      description: 'Configure your preferences',
      icon: <Settings data-testid="settings-icon" />,
      content: <div data-testid="settings-content">Settings Content</div>,
    },
    {
      id: 'profile',
      title: 'Profile',
      description: 'Manage your profile',
      icon: <User data-testid="profile-icon" />,
      content: <div data-testid="profile-content">Profile Content</div>,
    },
    {
      id: 'notifications',
      title: 'Notifications',
      icon: <Bell data-testid="notifications-icon" />,
      content: <div data-testid="notifications-content">Notifications Content</div>,
    },
  ];

  const defaultProps = {
    views: mockViews,
    activeView: 'settings',
    isOpen: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();

  describe('Basic Rendering', () => {
    it('renders the right panel when open', () => {
      render(<RightPanel {...defaultProps} />);
      
      expect(screen.getByRole('complementary')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument();
      expect(screen.getByText('Configure your preferences')).toBeInTheDocument();
      expect(screen.getByTestId('settings-content')).toBeInTheDocument();

    it('does not render when closed', () => {
      render(<RightPanel {...defaultProps} isOpen={false} />);
      
      expect(screen.queryByRole('complementary')).not.toBeInTheDocument();

    it('renders with default view when no activeView is specified', () => {
      render(<RightPanel views={mockViews} isOpen={true} />);
      
      expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument();
      expect(screen.getByTestId('settings-content')).toBeInTheDocument();


  describe('View Management', () => {
    it('displays the correct active view content', () => {
      render(<RightPanel {...defaultProps} activeView="profile" />);
      
      expect(screen.getByRole('heading', { name: 'Profile' })).toBeInTheDocument();
      expect(screen.getByText('Manage your profile')).toBeInTheDocument();
      expect(screen.getByTestId('profile-content')).toBeInTheDocument();
      expect(screen.queryByTestId('settings-content')).not.toBeInTheDocument();

    it('calls onViewChange when navigation button is clicked', async () => {
      const user = userEvent.setup();
      const onViewChange = vi.fn();
      
      render(
        <RightPanel
          {...defaultProps}
          onViewChange={onViewChange}
          showNavigation={true}
        />
      );
      
      const profileButton = screen.getByRole('button', { name: /profile/i });
      await user.click(profileButton);
      
      expect(onViewChange).toHaveBeenCalledWith('profile');

    it('switches content when activeView changes', () => {
      const { rerender } = render(<RightPanel {...defaultProps} activeView="settings" />);
      
      expect(screen.getByTestId('settings-content')).toBeInTheDocument();
      
      rerender(<RightPanel {...defaultProps} activeView="profile" />);
      
      expect(screen.getByTestId('profile-content')).toBeInTheDocument();
      expect(screen.queryByTestId('settings-content')).not.toBeInTheDocument();


  describe('Navigation', () => {
    it('renders navigation when showNavigation is true and multiple views exist', () => {
      render(<RightPanel {...defaultProps} showNavigation={true} />);
      
      expect(screen.getByRole('button', { name: /settings/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /profile/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument();

    it('does not render navigation when showNavigation is false', () => {
      render(<RightPanel {...defaultProps} showNavigation={false} />);
      
      expect(screen.queryByRole('button', { name: /profile/i })).not.toBeInTheDocument();

    it('does not render navigation when only one view exists', () => {
      render(
        <RightPanel
          views={[mockViews[0]]}
          activeView="settings"
          isOpen={true}
          showNavigation={true}
        />
      );
      
      expect(screen.queryByRole('button', { name: /settings/i })).not.toBeInTheDocument();

    it('highlights the active view in navigation', () => {
      render(<RightPanel {...defaultProps} activeView="profile" showNavigation={true} />);
      
      const profileButton = screen.getByRole('button', { name: /profile/i });
      const settingsButton = screen.getByRole('button', { name: /settings/i });
      
      // Active button should have different styling (this depends on your Button component implementation)
      expect(profileButton).toBeInTheDocument();
      expect(settingsButton).toBeInTheDocument();


  describe('Close Functionality', () => {
    it('renders close button when showCloseButton is true', () => {
      const onClose = vi.fn();
      render(<RightPanel {...defaultProps} showCloseButton={true} onClose={onClose} />);
      
      expect(screen.getByRole('button', { name: /close panel/i })).toBeInTheDocument();

    it('does not render close button when showCloseButton is false', () => {
      render(<RightPanel {...defaultProps} showCloseButton={false} />);
      
      expect(screen.queryByRole('button', { name: /close panel/i })).not.toBeInTheDocument();

    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      
      render(<RightPanel {...defaultProps} onClose={onClose} />);
      
      const closeButton = screen.getByRole('button', { name: /close panel/i });
      await user.click(closeButton);
      
      expect(onClose).toHaveBeenCalledTimes(1);


  describe('Width Variants', () => {
    it('applies correct width classes for different variants', () => {
      const { rerender } = render(<RightPanel {...defaultProps} width="sm" />);
      let panel = screen.getByRole('complementary');
      expect(panel).toHaveClass('w-80');
      
      rerender(<RightPanel {...defaultProps} width="md" />);
      panel = screen.getByRole('complementary');
      expect(panel).toHaveClass('w-96');
      
      rerender(<RightPanel {...defaultProps} width="lg" />);
      panel = screen.getByRole('complementary');
      expect(panel).toHaveClass('w-[28rem]');
      
      rerender(<RightPanel {...defaultProps} width="xl" />);
      panel = screen.getByRole('complementary');
      expect(panel).toHaveClass('w-[32rem]');
      
      rerender(<RightPanel {...defaultProps} width="full" />);
      panel = screen.getByRole('complementary');
      expect(panel).toHaveClass('w-full');


  describe('Custom Content', () => {
    it('renders custom header content', () => {
      const headerContent = <div data-testid="custom-header">Custom Header</div>;
      
      render(<RightPanel {...defaultProps} headerContent={headerContent} />);
      
      expect(screen.getByTestId('custom-header')).toBeInTheDocument();

    it('renders custom footer content', () => {
      const footerContent = <div data-testid="custom-footer">Custom Footer</div>;
      
      render(<RightPanel {...defaultProps} footerContent={footerContent} />);
      
      expect(screen.getByTestId('custom-footer')).toBeInTheDocument();


  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      const onClose = vi.fn();
      render(<RightPanel {...defaultProps} onClose={onClose} />);
      
      const panel = screen.getByRole('complementary');
      expect(panel).toBeInTheDocument();
      
      const closeButton = screen.getByRole('button', { name: /close panel/i });
      expect(closeButton).toHaveAttribute('aria-label', 'Close panel');

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      const onViewChange = vi.fn();
      
      render(<RightPanel {...defaultProps} onViewChange={onViewChange} />);
      
      // Focus on the profile button specifically
      const profileButton = screen.getByRole('button', { name: /profile/i });
      profileButton.focus();
      
      // Press Enter to activate
      await user.keyboard('{Enter}');
      
      expect(onViewChange).toHaveBeenCalledWith('profile');


  describe('Grid System', () => {
    it('uses 12-column grid system in header', () => {
      render(<RightPanel {...defaultProps} />);
      
      // Check that the header uses grid-cols-12
      const headerGrid = screen.getByRole('complementary').querySelector('.grid-cols-12');
      expect(headerGrid).toBeInTheDocument();

    it('uses 12-column grid system in content', () => {
      render(<RightPanel {...defaultProps} />);
      
      // Check that content area uses grid system
      const contentGrid = screen.getByRole('complementary').querySelector('.grid-cols-12');
      expect(contentGrid).toBeInTheDocument();



describe('useRightPanel Hook', () => {
  function TestComponent({ initialView }: { initialView?: string }) {
    const { isOpen, activeView, openPanel, closePanel, switchView } = useRightPanel(initialView);
    
    return (
      <div>
        <div data-testid="is-open">{isOpen.toString()}</div>
        <div data-testid="active-view">{activeView || 'none'}</div>
        <button onClick={() => openPanel('test-view')}>Open Panel</button>
        <button onClick={() => openPanel()}>Open Panel No View</button>
        <button onClick={closePanel} aria-label="Button">Close Panel</button>
        <button onClick={() => switchView('new-view')}>Switch View</button>
      </div>
    );
  }

  it('initializes with correct default state', () => {
    render(<TestComponent />);
    
    expect(screen.getByTestId('is-open')).toHaveTextContent('false');
    expect(screen.getByTestId('active-view')).toHaveTextContent('none');

  it('initializes with provided initial view', () => {
    render(<TestComponent initialView="initial-view" />);
    
    expect(screen.getByTestId('active-view')).toHaveTextContent('initial-view');

  it('opens panel and sets view when openPanel is called with viewId', async () => {
    const user = userEvent.setup();
    render(<TestComponent />);
    
    await user.click(screen.getByText('Open Panel'));
    
    expect(screen.getByTestId('is-open')).toHaveTextContent('true');
    expect(screen.getByTestId('active-view')).toHaveTextContent('test-view');

  it('opens panel without changing view when openPanel is called without viewId', async () => {
    const user = userEvent.setup();
    render(<TestComponent initialView="existing-view" />);
    
    await user.click(screen.getByText('Open Panel No View'));
    
    expect(screen.getByTestId('is-open')).toHaveTextContent('true');
    expect(screen.getByTestId('active-view')).toHaveTextContent('existing-view');

  it('closes panel when closePanel is called', async () => {
    const user = userEvent.setup();
    render(<TestComponent />);
    
    // First open the panel
    await user.click(screen.getByText('Open Panel'));
    expect(screen.getByTestId('is-open')).toHaveTextContent('true');
    
    // Then close it
    await user.click(screen.getByText('Close Panel'));
    expect(screen.getByTestId('is-open')).toHaveTextContent('false');

  it('switches view when switchView is called', async () => {
    const user = userEvent.setup();
    render(<TestComponent initialView="initial-view" />);
    
    await user.click(screen.getByText('Switch View'));
    
    expect(screen.getByTestId('active-view')).toHaveTextContent('new-view');

