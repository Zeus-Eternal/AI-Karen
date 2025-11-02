
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useFirstRunSetup } from '@/hooks/useFirstRunSetup';
import { SetupRouteGuard, useSetupRouteAccess, FirstRunRedirect } from '../SetupRouteGuard';

// Mock dependencies
import { vi } from 'vitest';

vi.mock('next/navigation');
vi.mock('@/hooks/useFirstRunSetup');

const mockRouter = {
  replace: vi.fn(),
  push: vi.fn(),
};

const mockUseFirstRunSetup = {
  isFirstRun: true,
  setupCompleted: false,
  isLoading: false,
  error: null,
};

describe('SetupRouteGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue(mockUseFirstRunSetup);

  describe('Access Control', () => {
    it('renders children when first run and setup not completed', () => {
      render(
        <SetupRouteGuard>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      expect(screen.getByText('Setup Content')).toBeInTheDocument();

    it('shows loading state when checking setup status', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        isLoading: true,

      render(
        <SetupRouteGuard>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      expect(screen.getByText('Checking Setup Status')).toBeInTheDocument();
      expect(screen.queryByText('Setup Content')).not.toBeInTheDocument();

    it('shows custom fallback when loading', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        isLoading: true,

      render(
        <SetupRouteGuard fallback={<div>Custom Loading</div>}>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      expect(screen.getByText('Custom Loading')).toBeInTheDocument();
      expect(screen.queryByText('Setup Content')).not.toBeInTheDocument();

    it('redirects to login when setup is completed', async () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        setupCompleted: true,

      render(
        <SetupRouteGuard>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalledWith('/login');

      expect(screen.queryByText('Setup Content')).not.toBeInTheDocument();

    it('redirects to login when not first run', async () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        isFirstRun: false,

      render(
        <SetupRouteGuard>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      await waitFor(() => {
        expect(mockRouter.replace).toHaveBeenCalledWith('/login');

      expect(screen.queryByText('Setup Content')).not.toBeInTheDocument();

    it('shows error state when setup check fails', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        error: 'Failed to check setup status',

      render(
        <SetupRouteGuard>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      expect(screen.getByText('Setup Check Failed')).toBeInTheDocument();
      expect(screen.getByText('Failed to check setup status')).toBeInTheDocument();
      expect(screen.queryByText('Setup Content')).not.toBeInTheDocument();


  describe('Error Handling', () => {
    it('provides refresh button when error occurs', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        error: 'Network error',

      // Mock window.location.reload
      const mockReload = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload: mockReload },
        writable: true,

      render(
        <SetupRouteGuard>
          <div>Setup Content</div>
        </SetupRouteGuard>
      );

      const refreshButton = screen.getByText('Refresh Page');
      refreshButton.click();

      expect(mockReload).toHaveBeenCalled();



describe('useSetupRouteAccess', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue(mockUseFirstRunSetup);

  it('returns correct access state when setup is allowed', () => {
    const TestComponent = () => {
      const { canAccessSetup, shouldRedirectToLogin, isCheckingAccess } = useSetupRouteAccess();
      
      return (
        <div>
          <div>Can Access: {canAccessSetup.toString()}</div>
          <div>Should Redirect: {shouldRedirectToLogin.toString()}</div>
          <div>Is Checking: {isCheckingAccess.toString()}</div>
        </div>
      );
    };

    render(<TestComponent />);

    expect(screen.getByText('Can Access: true')).toBeInTheDocument();
    expect(screen.getByText('Should Redirect: false')).toBeInTheDocument();
    expect(screen.getByText('Is Checking: false')).toBeInTheDocument();

  it('returns correct access state when setup is completed', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      setupCompleted: true,

    const TestComponent = () => {
      const { canAccessSetup, shouldRedirectToLogin, isCheckingAccess } = useSetupRouteAccess();
      
      return (
        <div>
          <div>Can Access: {canAccessSetup.toString()}</div>
          <div>Should Redirect: {shouldRedirectToLogin.toString()}</div>
          <div>Is Checking: {isCheckingAccess.toString()}</div>
        </div>
      );
    };

    render(<TestComponent />);

    expect(screen.getByText('Can Access: false')).toBeInTheDocument();
    expect(screen.getByText('Should Redirect: true')).toBeInTheDocument();
    expect(screen.getByText('Is Checking: false')).toBeInTheDocument();

  it('returns correct access state when loading', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      isLoading: true,

    const TestComponent = () => {
      const { canAccessSetup, shouldRedirectToLogin, isCheckingAccess } = useSetupRouteAccess();
      
      return (
        <div>
          <div>Can Access: {canAccessSetup.toString()}</div>
          <div>Should Redirect: {shouldRedirectToLogin.toString()}</div>
          <div>Is Checking: {isCheckingAccess.toString()}</div>
        </div>
      );
    };

    render(<TestComponent />);

    expect(screen.getByText('Can Access: false')).toBeInTheDocument();
    expect(screen.getByText('Should Redirect: false')).toBeInTheDocument();
    expect(screen.getByText('Is Checking: true')).toBeInTheDocument();


describe('FirstRunRedirect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue(mockUseFirstRunSetup);

  it('renders children when setup is completed', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      setupCompleted: true,

    render(
      <FirstRunRedirect>
        <div>App Content</div>
      </FirstRunRedirect>
    );

    expect(screen.getByText('App Content')).toBeInTheDocument();

  it('renders children when not first run', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      isFirstRun: false,

    render(
      <FirstRunRedirect>
        <div>App Content</div>
      </FirstRunRedirect>
    );

    expect(screen.getByText('App Content')).toBeInTheDocument();

  it('redirects to setup when first run and setup not completed', async () => {
    render(
      <FirstRunRedirect>
        <div>App Content</div>
      </FirstRunRedirect>
    );

    await waitFor(() => {
      expect(mockRouter.replace).toHaveBeenCalledWith('/setup');

    expect(screen.queryByText('App Content')).not.toBeInTheDocument();

  it('does not redirect when loading', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      isLoading: true,

    render(
      <FirstRunRedirect>
        <div>App Content</div>
      </FirstRunRedirect>
    );

    expect(mockRouter.replace).not.toHaveBeenCalled();
    expect(screen.getByText('App Content')).toBeInTheDocument();


describe('Accessibility', () => {
  it('has proper ARIA labels in loading state', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      isLoading: true,

    render(
      <SetupRouteGuard>
        <div>Setup Content</div>
      </SetupRouteGuard>
    );

    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Checking Setup Status');

  it('has proper ARIA labels in error state', () => {
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
      ...mockUseFirstRunSetup,
      error: 'Test error',

    render(
      <SetupRouteGuard>
        <div>Setup Content</div>
      </SetupRouteGuard>
    );

    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Setup Check Failed');
    expect(screen.getByRole('button')).toHaveTextContent('Refresh Page');

