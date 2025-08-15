import React from 'react';

export interface InlineErrorProps {
  message: string;
  field?: string;
  variant?: 'error' | 'warning' | 'info';
  size?: 'small' | 'medium' | 'large';
  showIcon?: boolean;
  className?: string;
  id?: string;
  'aria-live'?: 'polite' | 'assertive' | 'off';
}

export const InlineError: React.FC<InlineErrorProps> = ({
  message,
  field,
  variant = 'error',
  size = 'medium',
  showIcon = true,
  className = '',
  id,
  'aria-live': ariaLive = 'polite',
}) => {
  const getIcon = () => {
    if (!showIcon) return null;

    switch (variant) {
      case 'error':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        );
      case 'warning':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        );
      case 'info':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
          </svg>
        );
      default:
        return null;
    }
  };

  const classes = [
    'inline-error',
    `inline-error--${variant}`,
    `inline-error--${size}`,
    className,
  ].filter(Boolean).join(' ');

  return (
    <div
      className={classes}
      role="alert"
      aria-live={ariaLive}
      id={id}
      aria-describedby={field ? `${field}-error` : undefined}
    >
      {showIcon && (
        <div className="inline-error__icon">
          {getIcon()}
        </div>
      )}
      <span className="inline-error__message">
        {message}
      </span>
    </div>
  );
};

export interface FieldErrorProps extends Omit<InlineErrorProps, 'field'> {
  field: string;
  errors?: string | string[];
  touched?: boolean;
  showWhen?: 'always' | 'touched' | 'dirty';
}

export const FieldError: React.FC<FieldErrorProps> = ({
  field,
  errors,
  touched = false,
  showWhen = 'touched',
  ...props
}) => {
  const shouldShow = () => {
    if (!errors) return false;
    
    switch (showWhen) {
      case 'always':
        return true;
      case 'touched':
        return touched;
      case 'dirty':
        return touched; // Assuming touched implies dirty for simplicity
      default:
        return false;
    }
  };

  if (!shouldShow()) {
    return null;
  }

  const errorMessage = Array.isArray(errors) ? errors[0] : errors;

  return (
    <InlineError
      {...props}
      field={field}
      message={errorMessage}
      id={`${field}-error`}
    />
  );
};

export interface ValidationSummaryProps {
  errors: Record<string, string | string[]>;
  title?: string;
  className?: string;
  maxErrors?: number;
  showFieldNames?: boolean;
}

export const ValidationSummary: React.FC<ValidationSummaryProps> = ({
  errors,
  title = 'Please correct the following errors:',
  className = '',
  maxErrors = 10,
  showFieldNames = true,
}) => {
  const errorEntries = Object.entries(errors).filter(([, error]) => error);
  
  if (errorEntries.length === 0) {
    return null;
  }

  const displayErrors = errorEntries.slice(0, maxErrors);
  const hasMoreErrors = errorEntries.length > maxErrors;

  return (
    <div className={`validation-summary ${className}`} role="alert" aria-live="polite">
      <div className="validation-summary__header">
        <div className="validation-summary__icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h3 className="validation-summary__title">{title}</h3>
      </div>
      
      <ul className="validation-summary__list">
        {displayErrors.map(([field, error]) => {
          const errorMessage = Array.isArray(error) ? error[0] : error;
          return (
            <li key={field} className="validation-summary__item">
              {showFieldNames && (
                <strong className="validation-summary__field">
                  {field.charAt(0).toUpperCase() + field.slice(1)}:
                </strong>
              )}{' '}
              {errorMessage}
            </li>
          );
        })}
      </ul>
      
      {hasMoreErrors && (
        <div className="validation-summary__more">
          And {errorEntries.length - maxErrors} more error{errorEntries.length - maxErrors !== 1 ? 's' : ''}...
        </div>
      )}
    </div>
  );
};

export default InlineError;