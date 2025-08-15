import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { InlineError, FieldError, ValidationSummary } from '../InlineError';

describe('InlineError', () => {
  it('renders basic error correctly', () => {
    render(
      <InlineError
        message="This is an error message"
        variant="error"
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('This is an error message')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('inline-error--error');
  });

  it('renders different variants correctly', () => {
    const { rerender } = render(
      <InlineError message="Error message" variant="error" />
    );
    expect(screen.getByRole('alert')).toHaveClass('inline-error--error');

    rerender(<InlineError message="Warning message" variant="warning" />);
    expect(screen.getByRole('alert')).toHaveClass('inline-error--warning');

    rerender(<InlineError message="Info message" variant="info" />);
    expect(screen.getByRole('alert')).toHaveClass('inline-error--info');
  });

  it('renders different sizes correctly', () => {
    const { rerender } = render(
      <InlineError message="Small error" size="small" />
    );
    expect(screen.getByRole('alert')).toHaveClass('inline-error--small');

    rerender(<InlineError message="Medium error" size="medium" />);
    expect(screen.getByRole('alert')).toHaveClass('inline-error--medium');

    rerender(<InlineError message="Large error" size="large" />);
    expect(screen.getByRole('alert')).toHaveClass('inline-error--large');
  });

  it('shows/hides icon correctly', () => {
    const { rerender } = render(
      <InlineError message="With icon" showIcon={true} />
    );
    expect(screen.getByRole('alert').querySelector('.inline-error__icon')).toBeInTheDocument();

    rerender(<InlineError message="Without icon" showIcon={false} />);
    expect(screen.getByRole('alert').querySelector('.inline-error__icon')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <InlineError
        message="Custom class error"
        className="custom-error-class"
      />
    );

    expect(screen.getByRole('alert')).toHaveClass('custom-error-class');
  });

  it('sets correct accessibility attributes', () => {
    render(
      <InlineError
        message="Accessible error"
        field="username"
        id="username-error"
        aria-live="assertive"
      />
    );

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'assertive');
    expect(alert).toHaveAttribute('id', 'username-error');
    expect(alert).toHaveAttribute('aria-describedby', 'username-error');
  });
});

describe('FieldError', () => {
  it('shows error when touched and has errors', () => {
    render(
      <FieldError
        field="email"
        errors="Invalid email format"
        touched={true}
        showWhen="touched"
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveAttribute('id', 'email-error');
  });

  it('hides error when not touched', () => {
    render(
      <FieldError
        field="email"
        errors="Invalid email format"
        touched={false}
        showWhen="touched"
      />
    );

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows error always when showWhen is always', () => {
    render(
      <FieldError
        field="email"
        errors="Invalid email format"
        touched={false}
        showWhen="always"
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Invalid email format')).toBeInTheDocument();
  });

  it('handles array of errors', () => {
    render(
      <FieldError
        field="password"
        errors={['Too short', 'Must contain numbers']}
        touched={true}
      />
    );

    expect(screen.getByText('Too short')).toBeInTheDocument();
    expect(screen.queryByText('Must contain numbers')).not.toBeInTheDocument(); // Only shows first error
  });

  it('hides when no errors', () => {
    render(
      <FieldError
        field="email"
        errors=""
        touched={true}
      />
    );

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('hides when errors is undefined', () => {
    render(
      <FieldError
        field="email"
        errors={undefined}
        touched={true}
      />
    );

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

describe('ValidationSummary', () => {
  const mockErrors = {
    email: 'Invalid email format',
    password: 'Password too short',
    confirmPassword: 'Passwords do not match',
  };

  it('renders validation summary with errors', () => {
    render(<ValidationSummary errors={mockErrors} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Please correct the following errors:')).toBeInTheDocument();
    expect(screen.getByText(/Invalid email format/)).toBeInTheDocument();
    expect(screen.getByText(/Password too short/)).toBeInTheDocument();
    expect(screen.getByText(/Passwords do not match/)).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(
      <ValidationSummary
        errors={mockErrors}
        title="Fix these issues:"
      />
    );

    expect(screen.getByText('Fix these issues:')).toBeInTheDocument();
  });

  it('shows field names when enabled', () => {
    render(
      <ValidationSummary
        errors={mockErrors}
        showFieldNames={true}
      />
    );

    expect(screen.getByText(/Email:/)).toBeInTheDocument();
    expect(screen.getByText(/Password:/)).toBeInTheDocument();
    expect(screen.getByText(/ConfirmPassword:/)).toBeInTheDocument();
  });

  it('hides field names when disabled', () => {
    render(
      <ValidationSummary
        errors={mockErrors}
        showFieldNames={false}
      />
    );

    expect(screen.queryByText(/Email:/)).not.toBeInTheDocument();
    expect(screen.getByText('Invalid email format')).toBeInTheDocument();
  });

  it('limits number of errors displayed', () => {
    render(
      <ValidationSummary
        errors={mockErrors}
        maxErrors={2}
      />
    );

    const listItems = screen.getAllByRole('listitem');
    expect(listItems).toHaveLength(2);
    expect(screen.getByText('And 1 more error...')).toBeInTheDocument();
  });

  it('handles multiple errors in maxErrors message', () => {
    const manyErrors = {
      field1: 'Error 1',
      field2: 'Error 2',
      field3: 'Error 3',
      field4: 'Error 4',
      field5: 'Error 5',
    };

    render(
      <ValidationSummary
        errors={manyErrors}
        maxErrors={2}
      />
    );

    expect(screen.getByText('And 3 more errors...')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <ValidationSummary
        errors={mockErrors}
        className="custom-validation-class"
      />
    );

    expect(screen.getByRole('alert')).toHaveClass('custom-validation-class');
  });

  it('does not render when no errors', () => {
    render(<ValidationSummary errors={{}} />);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('filters out empty errors', () => {
    const errorsWithEmpty = {
      email: 'Invalid email',
      password: '',
      username: undefined as any,
      phone: 'Invalid phone',
    };

    render(<ValidationSummary errors={errorsWithEmpty} />);

    expect(screen.getByText(/Invalid email/)).toBeInTheDocument();
    expect(screen.getByText(/Invalid phone/)).toBeInTheDocument();
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/username/i)).not.toBeInTheDocument();
  });

  it('handles array errors in summary', () => {
    const errorsWithArrays = {
      email: ['Invalid format', 'Already exists'],
      password: 'Too short',
    };

    render(<ValidationSummary errors={errorsWithArrays} />);

    expect(screen.getByText(/Invalid format/)).toBeInTheDocument();
    expect(screen.queryByText(/Already exists/)).not.toBeInTheDocument(); // Only shows first error
    expect(screen.getByText(/Too short/)).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    render(<ValidationSummary errors={mockErrors} />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'polite');
    expect(alert).toHaveClass('validation-summary');
  });
});