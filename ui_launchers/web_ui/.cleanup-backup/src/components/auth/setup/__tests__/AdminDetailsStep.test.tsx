import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminDetailsStep } from '../steps/AdminDetailsStep';
import type { SetupStepProps } from '../SetupWizard';

// Mock the validation functions
import { vi } from 'vitest';

vi.mock('@/lib/auth/setup-validation', () => ({
  validateSuperAdminCreation: vi.fn(),
  calculatePasswordStrength: vi.fn(),
}));

import { validateSuperAdminCreation, calculatePasswordStrength } from '@/lib/auth/setup-validation';

const mockValidateSuperAdminCreation = validateSuperAdminCreation as ReturnType<typeof vi.fn>;
const mockCalculatePasswordStrength = calculatePasswordStrength as ReturnType<typeof vi.fn>;

const defaultProps: SetupStepProps = {
  formData: {
    email: '',
    full_name: '',
    password: '',
    confirm_password: '',
  },
  onFormDataChange: vi.fn(),
  onNext: vi.fn(),
  onPrevious: vi.fn(),
  isLoading: false,
  error: null,
  onClearError: vi.fn(),
};

describe('AdminDetailsStep', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    mockValidateSuperAdminCreation.mockResolvedValue({
      isValid: true,
      errors: {},
    });
    
    mockCalculatePasswordStrength.mockReturnValue({
      score: 6,
      level: 'strong',
      feedback: [],
    });
  });

  describe('Form Rendering', () => {
    it('renders all form fields', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('renders submit button', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      expect(screen.getByText('Create Super Admin Account')).toBeInTheDocument();
    });

    it('renders password requirements', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      expect(screen.getByText('Password Requirements:')).toBeInTheDocument();
      expect(screen.getByText('At least 12 characters long')).toBeInTheDocument();
      expect(screen.getByText('Contains lowercase letters')).toBeInTheDocument();
      expect(screen.getByText('Contains uppercase letters')).toBeInTheDocument();
      expect(screen.getByText('Contains numbers')).toBeInTheDocument();
      expect(screen.getByText('Contains special characters')).toBeInTheDocument();
    });
  });

  describe('Form Interaction', () => {
    it('calls onFormDataChange when input values change', () => {
      const mockOnFormDataChange = vi.fn();
      render(<AdminDetailsStep {...defaultProps} onFormDataChange={mockOnFormDataChange} />);

      const nameInput = screen.getByLabelText(/full name/i);
      fireEvent.change(nameInput, { target: { value: 'John Doe' } });

      expect(mockOnFormDataChange).toHaveBeenCalledWith({ full_name: 'John Doe' });
    });

    it('calls onClearError when input values change', () => {
      const mockOnClearError = vi.fn();
      render(<AdminDetailsStep {...defaultProps} onClearError={mockOnClearError} />);

      const emailInput = screen.getByLabelText(/email address/i);
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

      expect(mockOnClearError).toHaveBeenCalled();
    });

    it('toggles password visibility', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      const passwordInput = screen.getByLabelText(/^password$/i);
      const toggleButton = passwordInput.parentElement?.querySelector('button');

      expect(passwordInput).toHaveAttribute('type', 'password');

      if (toggleButton) {
        fireEvent.click(toggleButton);
        expect(passwordInput).toHaveAttribute('type', 'text');

        fireEvent.click(toggleButton);
        expect(passwordInput).toHaveAttribute('type', 'password');
      }
    });

    it('toggles confirm password visibility', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const toggleButton = confirmPasswordInput.parentElement?.querySelector('button');

      expect(confirmPasswordInput).toHaveAttribute('type', 'password');

      if (toggleButton) {
        fireEvent.click(toggleButton);
        expect(confirmPasswordInput).toHaveAttribute('type', 'text');
      }
    });
  });

  describe('Password Strength Indicator', () => {
    it('shows password strength when password is entered', async () => {
      const propsWithPassword = {
        ...defaultProps,
        formData: { ...defaultProps.formData, password: 'TestPassword123!' },
      };

      render(<AdminDetailsStep {...propsWithPassword} />);

      await waitFor(() => {
        expect(screen.getByText('Password Strength:')).toBeInTheDocument();
        expect(screen.getByText('Strong')).toBeInTheDocument();
      });
    });

    it('shows password strength feedback', async () => {
      mockCalculatePasswordStrength.mockReturnValue({
        score: 3,
        level: 'medium',
        feedback: ['Add more special characters', 'Make it longer'],
      });

      const propsWithPassword = {
        ...defaultProps,
        formData: { ...defaultProps.formData, password: 'password123' },
      };

      render(<AdminDetailsStep {...propsWithPassword} />);

      await waitFor(() => {
        expect(screen.getByText('Suggestions:')).toBeInTheDocument();
        expect(screen.getByText('Add more special characters')).toBeInTheDocument();
        expect(screen.getByText('Make it longer')).toBeInTheDocument();
      });
    });

    it('shows different colors for different strength levels', async () => {
      const strengthLevels = [
        { level: 'very_weak', color: 'bg-red-500' },
        { level: 'weak', color: 'bg-orange-500' },
        { level: 'medium', color: 'bg-yellow-500' },
        { level: 'strong', color: 'bg-blue-500' },
        { level: 'very_strong', color: 'bg-green-500' },
      ] as const;

      for (const { level, color } of strengthLevels) {
        mockCalculatePasswordStrength.mockReturnValue({
          score: 4,
          level,
          feedback: [],
        });

        const propsWithPassword = {
          ...defaultProps,
          formData: { ...defaultProps.formData, password: 'test' },
        };

        const { rerender } = render(<AdminDetailsStep {...propsWithPassword} />);

        await waitFor(() => {
          const strengthBar = document.querySelector(`.${color}`);
          expect(strengthBar).toBeInTheDocument();
        });

        rerender(<div />); // Clear for next iteration
      }
    });
  });

  describe('Password Match Indicator', () => {
    it('shows passwords match when they are identical', async () => {
      const propsWithMatchingPasswords = {
        ...defaultProps,
        formData: {
          ...defaultProps.formData,
          password: 'TestPassword123!',
          confirm_password: 'TestPassword123!',
        },
      };

      render(<AdminDetailsStep {...propsWithMatchingPasswords} />);

      await waitFor(() => {
        expect(screen.getByText('Passwords match')).toBeInTheDocument();
      });
    });

    it('shows passwords do not match when they are different', async () => {
      const propsWithNonMatchingPasswords = {
        ...defaultProps,
        formData: {
          ...defaultProps.formData,
          password: 'TestPassword123!',
          confirm_password: 'DifferentPassword123!',
        },
      };

      render(<AdminDetailsStep {...propsWithNonMatchingPasswords} />);

      await waitFor(() => {
        expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
      });
    });
  });

  describe('Password Requirements Validation', () => {
    it('shows green checkmarks for met requirements', () => {
      const propsWithStrongPassword = {
        ...defaultProps,
        formData: {
          ...defaultProps.formData,
          password: 'TestPassword123!',
        },
      };

      render(<AdminDetailsStep {...propsWithStrongPassword} />);

      // All requirements should be met for this password
      // Look for green checkmark icons in the password requirements section
      const requirementsList = screen.getByText('Password Requirements:').closest('.bg-blue-50, .dark\\:bg-blue-950\\/20');
      const greenIcons = requirementsList?.querySelectorAll('.text-green-600') || [];
      
      // Should have multiple green checkmarks
      expect(greenIcons.length).toBeGreaterThan(0);
    });

    it('shows red X marks for unmet requirements', () => {
      const propsWithWeakPassword = {
        ...defaultProps,
        formData: {
          ...defaultProps.formData,
          password: 'weak',
        },
      };

      render(<AdminDetailsStep {...propsWithWeakPassword} />);

      // Most requirements should not be met for this password
      // Look for red X icons in the password requirements section
      const requirementsList = screen.getByText('Password Requirements:').closest('.bg-blue-50, .dark\\:bg-blue-950\\/20');
      const redIcons = requirementsList?.querySelectorAll('.text-red-600') || [];
      
      // Should have multiple red X marks
      expect(redIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Form Validation', () => {
    it('shows validation errors', async () => {
      mockValidateSuperAdminCreation.mockResolvedValue({
        isValid: false,
        errors: {
          email: 'Please enter a valid email address',
          password: 'Password is too weak',
        },
      });

      const propsWithInvalidData = {
        ...defaultProps,
        formData: {
          email: 'invalid-email',
          full_name: 'Test User',
          password: 'weak',
          confirm_password: 'weak',
        },
      };

      render(<AdminDetailsStep {...propsWithInvalidData} />);

      await waitFor(() => {
        expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
        expect(screen.getByText('Password is too weak')).toBeInTheDocument();
      });
    });

    it('disables submit button when form is invalid', async () => {
      mockValidateSuperAdminCreation.mockResolvedValue({
        isValid: false,
        errors: { email: 'Invalid email' },
      });

      render(<AdminDetailsStep {...defaultProps} />);

      await waitFor(() => {
        const submitButton = screen.getByText('Create Super Admin Account');
        expect(submitButton).toBeDisabled();
      });
    });

    it('enables submit button when form is valid', async () => {
      mockValidateSuperAdminCreation.mockResolvedValue({
        isValid: true,
        errors: {},
      });

      const propsWithValidData = {
        ...defaultProps,
        formData: {
          email: 'admin@test.com',
          full_name: 'Test Admin',
          password: 'TestPassword123!',
          confirm_password: 'TestPassword123!',
        },
      };

      render(<AdminDetailsStep {...propsWithValidData} />);

      await waitFor(() => {
        const submitButton = screen.getByText('Create Super Admin Account');
        expect(submitButton).not.toBeDisabled();
      });
    });
  });

  describe('Form Submission', () => {
    it('calls onNext when form is submitted with valid data', async () => {
      const mockOnNext = vi.fn();
      
      mockValidateSuperAdminCreation.mockResolvedValue({
        isValid: true,
        errors: {},
      });

      const propsWithValidData = {
        ...defaultProps,
        onNext: mockOnNext,
        formData: {
          email: 'admin@test.com',
          full_name: 'Test Admin',
          password: 'TestPassword123!',
          confirm_password: 'TestPassword123!',
        },
      };

      render(<AdminDetailsStep {...propsWithValidData} />);

      const submitButton = screen.getByText('Create Super Admin Account');
      const form = submitButton.closest('form');
      if (form) {
        fireEvent.submit(form);
      } else {
        fireEvent.click(submitButton);
      }

      await waitFor(() => {
        expect(mockOnNext).toHaveBeenCalled();
      });
    });

    it('does not call onNext when form is submitted with invalid data', async () => {
      const mockOnNext = vi.fn();
      
      mockValidateSuperAdminCreation.mockResolvedValue({
        isValid: false,
        errors: { email: 'Invalid email' },
      });

      const propsWithInvalidData = {
        ...defaultProps,
        onNext: mockOnNext,
        formData: {
          email: 'invalid-email',
          full_name: 'Test Admin',
          password: 'TestPassword123!',
          confirm_password: 'TestPassword123!',
        },
      };

      render(<AdminDetailsStep {...propsWithInvalidData} />);

      const submitButton = screen.getByText('Create Super Admin Account');
      const form = submitButton.closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      await waitFor(() => {
        expect(mockOnNext).not.toHaveBeenCalled();
      });
    });
  });

  describe('Loading State', () => {
    it('shows loading state when isLoading is true', () => {
      const propsWithLoading = {
        ...defaultProps,
        isLoading: true,
      };

      render(<AdminDetailsStep {...propsWithLoading} />);

      expect(screen.getByText('Creating Admin Account...')).toBeInTheDocument();
    });

    it('disables form inputs when loading', () => {
      const propsWithLoading = {
        ...defaultProps,
        isLoading: true,
      };

      render(<AdminDetailsStep {...propsWithLoading} />);

      expect(screen.getByLabelText(/full name/i)).toBeDisabled();
      expect(screen.getByLabelText(/email address/i)).toBeDisabled();
      expect(screen.getByLabelText(/^password$/i)).toBeDisabled();
      expect(screen.getByLabelText(/confirm password/i)).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('has proper labels for all form fields', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    it('has proper ARIA attributes for password fields', () => {
      render(<AdminDetailsStep {...defaultProps} />);

      const passwordInput = screen.getByLabelText(/^password$/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      expect(passwordInput).toHaveAttribute('autoComplete', 'new-password');
      expect(confirmPasswordInput).toHaveAttribute('autoComplete', 'new-password');
    });

    it('shows validation errors with proper ARIA attributes', async () => {
      mockValidateSuperAdminCreation.mockResolvedValue({
        isValid: false,
        errors: {
          email: 'Please enter a valid email address',
        },
      });

      const propsWithInvalidData = {
        ...defaultProps,
        formData: {
          ...defaultProps.formData,
          email: 'invalid-email',
        },
      };

      render(<AdminDetailsStep {...propsWithInvalidData} />);

      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email address/i);
        expect(emailInput).toHaveClass('border-red-500');
      });
    });
  });
});