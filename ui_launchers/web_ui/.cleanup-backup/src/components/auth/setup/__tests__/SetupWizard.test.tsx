import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useFirstRunSetup } from '@/hooks/useFirstRunSetup';
import { useAuth } from '@/contexts/AuthContext';
import { SetupWizard } from '../SetupWizard';

// Mock dependencies
import { vi } from 'vitest';

vi.mock('next/navigation');
vi.mock('@/hooks/useFirstRunSetup');
vi.mock('@/contexts/AuthContext');

const mockRouter = {
  replace: vi.fn(),
  push: vi.fn(),
};

const mockUseFirstRunSetup = {
  isFirstRun: true,
  setupCompleted: false,
  markSetupCompleted: vi.fn(),
  isLoading: false,
  error: null,
};

const mockUseAuth = {
  login: vi.fn(),
  user: null,
  isAuthenticated: false,
};

// Mock fetch
global.fetch = vi.fn();

describe('SetupWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useRouter as ReturnType<typeof vi.fn>).mockReturnValue(mockRouter);
    (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue(mockUseFirstRunSetup);
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue(mockUseAuth);
  });

  describe('Initial Render', () => {
    it('renders welcome step by default', () => {
      render(<SetupWizard />);
      
      expect(screen.getByText('Welcome to AI Karen!')).toBeInTheDocument();
      expect(screen.getByText('Step 1 of 4')).toBeInTheDocument();
      expect(screen.getByText('Get Started')).toBeInTheDocument();
    });

    it('shows loading state when setup is loading', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        isLoading: true,
      });

      render(<SetupWizard />);
      
      expect(screen.getByText('Checking setup status...')).toBeInTheDocument();
    });

    it('redirects to login when setup is completed', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        setupCompleted: true,
      });

      render(<SetupWizard />);
      
      expect(mockRouter.replace).toHaveBeenCalledWith('/login');
    });

    it('redirects to login when not first run', () => {
      (useFirstRunSetup as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockUseFirstRunSetup,
        isFirstRun: false,
      });

      render(<SetupWizard />);
      
      expect(mockRouter.replace).toHaveBeenCalledWith('/login');
    });
  });

  describe('Navigation', () => {
    it('navigates to admin details step when clicking next from welcome', async () => {
      render(<SetupWizard />);
      
      const nextButton = screen.getByText('Get Started');
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
        expect(screen.getByText('Step 2 of 4')).toBeInTheDocument();
      });
    });

    it('navigates back to welcome step when clicking previous from admin details', async () => {
      render(<SetupWizard />);
      
      // Go to admin details step
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
      });
      
      // Go back to welcome step
      const previousButton = screen.getByText('Previous');
      fireEvent.click(previousButton);
      
      await waitFor(() => {
        expect(screen.getByText('Welcome to AI Karen!')).toBeInTheDocument();
      });
    });

    it('disables previous button on first step', () => {
      render(<SetupWizard />);
      
      const previousButton = screen.getByText('Previous');
      expect(previousButton).toBeDisabled();
    });
  });

  describe('Admin Details Step', () => {
    beforeEach(async () => {
      render(<SetupWizard />);
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
      });
    });

    it('renders admin details form fields', () => {
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('shows password strength indicator when typing password', async () => {
      const passwordInput = screen.getByLabelText(/^password$/i);
      
      fireEvent.change(passwordInput, { target: { value: 'weakpass' } });
      
      await waitFor(() => {
        expect(screen.getByText('Password Strength:')).toBeInTheDocument();
      });
    });

    it('shows password match indicator', async () => {
      const passwordInput = screen.getByLabelText(/^password$/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      
      fireEvent.change(passwordInput, { target: { value: 'TestPassword123!' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'TestPassword123!' } });
      
      await waitFor(() => {
        expect(screen.getByText('Passwords match')).toBeInTheDocument();
      });
    });

    it('calls create super admin API when form is valid and submitted', async () => {
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} }),
      };
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      // Fill out the form
      fireEvent.change(screen.getByLabelText(/full name/i), { 
        target: { value: 'Test Admin' } 
      });
      fireEvent.change(screen.getByLabelText(/email address/i), { 
        target: { value: 'admin@test.com' } 
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), { 
        target: { value: 'TestPassword123!' } 
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), { 
        target: { value: 'TestPassword123!' } 
      });

      // Submit the form
      const submitButton = screen.getByText('Create Super Admin Account');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/admin/setup/create-super-admin', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: 'admin@test.com',
            full_name: 'Test Admin',
            password: 'TestPassword123!',
            confirm_password: 'TestPassword123!',
          }),
        });
      });
    });
  });

  describe('Email Verification Step', () => {
    beforeEach(async () => {
      render(<SetupWizard />);
      
      // Navigate to email verification step
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
      });

      // Mock successful admin creation
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} }),
      };
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      // Fill and submit admin details form
      fireEvent.change(screen.getByLabelText(/full name/i), { 
        target: { value: 'Test Admin' } 
      });
      fireEvent.change(screen.getByLabelText(/email address/i), { 
        target: { value: 'admin@test.com' } 
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), { 
        target: { value: 'TestPassword123!' } 
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), { 
        target: { value: 'TestPassword123!' } 
      });

      fireEvent.click(screen.getByText('Create Super Admin Account'));

      await waitFor(() => {
        expect(screen.getByText('Email Verification')).toBeInTheDocument();
      });
    });

    it('renders email verification form', () => {
      expect(screen.getByText('Verification Email Sent')).toBeInTheDocument();
      expect(screen.getByLabelText(/verification code/i)).toBeInTheDocument();
      expect(screen.getByText('Verify Email')).toBeInTheDocument();
    });

    it('allows entering 6-digit verification code', () => {
      const codeInput = screen.getByLabelText(/verification code/i);
      
      fireEvent.change(codeInput, { target: { value: '123456' } });
      
      expect(codeInput).toHaveValue('123456');
    });

    it('limits verification code to 6 digits', () => {
      const codeInput = screen.getByLabelText(/verification code/i);
      
      fireEvent.change(codeInput, { target: { value: '1234567890' } });
      
      expect(codeInput).toHaveValue('123456');
    });

    it('enables verify button when 6-digit code is entered', () => {
      const codeInput = screen.getByLabelText(/verification code/i);
      const verifyButton = screen.getByText('Verify Email');
      
      expect(verifyButton).toBeDisabled();
      
      fireEvent.change(codeInput, { target: { value: '123456' } });
      
      expect(verifyButton).not.toBeDisabled();
    });

    it('allows skipping verification for demo', () => {
      const skipButton = screen.getByText('Skip Verification (Demo Only)');
      
      fireEvent.click(skipButton);
      
      // Should navigate to completion step
      expect(screen.getByText('Setup Complete!')).toBeInTheDocument();
    });
  });

  describe('Setup Complete Step', () => {
    beforeEach(async () => {
      render(<SetupWizard />);
      
      // Navigate through all steps to completion
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
      });

      // Mock successful admin creation
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} }),
      };
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      // Fill and submit admin details
      fireEvent.change(screen.getByLabelText(/full name/i), { 
        target: { value: 'Test Admin' } 
      });
      fireEvent.change(screen.getByLabelText(/email address/i), { 
        target: { value: 'admin@test.com' } 
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), { 
        target: { value: 'TestPassword123!' } 
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), { 
        target: { value: 'TestPassword123!' } 
      });

      fireEvent.click(screen.getByText('Create Super Admin Account'));

      await waitFor(() => {
        expect(screen.getByText('Email Verification')).toBeInTheDocument();
      });

      // Skip email verification
      fireEvent.click(screen.getByText('Skip Verification (Demo Only)'));

      await waitFor(() => {
        expect(screen.getByText('Setup Complete!')).toBeInTheDocument();
      });
    });

    it('renders setup completion message', () => {
      expect(screen.getByText('Setup Complete!')).toBeInTheDocument();
      expect(screen.getByText('Your AI Karen system is now ready for action')).toBeInTheDocument();
    });

    it('shows completed features', () => {
      expect(screen.getByText('Super Admin Account Created')).toBeInTheDocument();
      expect(screen.getByText('User Management Enabled')).toBeInTheDocument();
      expect(screen.getByText('System Configuration Ready')).toBeInTheDocument();
    });

    it('shows account summary', () => {
      expect(screen.getByText('admin@test.com')).toBeInTheDocument();
      expect(screen.getByText('Test Admin')).toBeInTheDocument();
      expect(screen.getByText('Super Administrator')).toBeInTheDocument();
    });

    it('completes setup and logs in when clicking complete button', async () => {
      mockUseAuth.login.mockResolvedValue(undefined);

      const completeButton = screen.getByText('Enter AI Karen Dashboard');
      fireEvent.click(completeButton);

      await waitFor(() => {
        expect(mockUseFirstRunSetup.markSetupCompleted).toHaveBeenCalled();
        expect(mockUseAuth.login).toHaveBeenCalledWith({
          email: 'admin@test.com',
          password: 'TestPassword123!',
        });
        expect(mockRouter.replace).toHaveBeenCalledWith('/admin');
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error when super admin creation fails', async () => {
      render(<SetupWizard />);
      
      // Navigate to admin details step
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
      });

      // Mock failed API response
      const mockResponse = {
        ok: false,
        json: () => Promise.resolve({ 
          success: false, 
          error: { message: 'Email already exists' } 
        }),
      };
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      // Fill and submit form
      fireEvent.change(screen.getByLabelText(/full name/i), { 
        target: { value: 'Test Admin' } 
      });
      fireEvent.change(screen.getByLabelText(/email address/i), { 
        target: { value: 'admin@test.com' } 
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), { 
        target: { value: 'TestPassword123!' } 
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), { 
        target: { value: 'TestPassword123!' } 
      });

      fireEvent.click(screen.getByText('Create Super Admin Account'));

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument();
      });
    });

    it('clears error when user makes changes', async () => {
      render(<SetupWizard />);
      
      // Navigate to admin details step
      fireEvent.click(screen.getByText('Get Started'));
      
      await waitFor(() => {
        expect(screen.getByText('Admin Details')).toBeInTheDocument();
      });

      // Mock failed API response
      const mockResponse = {
        ok: false,
        json: () => Promise.resolve({ 
          success: false, 
          error: { message: 'Email already exists' } 
        }),
      };
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      // Fill and submit form to trigger error
      fireEvent.change(screen.getByLabelText(/full name/i), { 
        target: { value: 'Test Admin' } 
      });
      fireEvent.change(screen.getByLabelText(/email address/i), { 
        target: { value: 'admin@test.com' } 
      });
      fireEvent.change(screen.getByLabelText(/^password$/i), { 
        target: { value: 'TestPassword123!' } 
      });
      fireEvent.change(screen.getByLabelText(/confirm password/i), { 
        target: { value: 'TestPassword123!' } 
      });

      fireEvent.click(screen.getByText('Create Super Admin Account'));

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument();
      });

      // Make a change to clear error
      fireEvent.change(screen.getByLabelText(/email address/i), { 
        target: { value: 'admin2@test.com' } 
      });

      await waitFor(() => {
        expect(screen.queryByText('Email already exists')).not.toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    it('renders properly on mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<SetupWizard />);
      
      expect(screen.getByText('Welcome to AI Karen!')).toBeInTheDocument();
      
      // Check that responsive classes are applied
      const progressSteps = screen.getAllByText(/Step \d of 4/);
      expect(progressSteps).toHaveLength(1);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<SetupWizard />);
      
      // Check for proper heading structure
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('AI Karen Setup');
      
      // Check for progress indicator
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(<SetupWizard />);
      
      const nextButton = screen.getByText('Get Started');
      
      // Focus should be manageable via keyboard
      nextButton.focus();
      expect(document.activeElement).toBe(nextButton);
    });
  });
});