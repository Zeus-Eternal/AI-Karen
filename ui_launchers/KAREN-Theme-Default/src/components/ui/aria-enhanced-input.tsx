/**
 * ARIA Enhanced Input Component
 * Extends the base input with comprehensive accessibility features
 */
import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  createFormAria,
  createAriaLabel,
  mergeAriaProps,
  type AriaProps
} from "@/utils/aria";
export interface AriaEnhancedInputProps extends React.ComponentProps<"input"> {
  /** Accessible label for the input */
  ariaLabel?: string;
  /** ID of element that labels this input */
  ariaLabelledBy?: string;
  /** ID of element that describes this input */
  ariaDescribedBy?: string;
  /** Whether the input is invalid */
  invalid?: boolean | 'grammar' | 'spelling';
  /** Whether the input is required */
  required?: boolean;
  /** ID of error message element */
  errorId?: string;
  /** ID of help text element */
  helpId?: string;
  /** Custom ARIA props */
  ariaProps?: Partial<AriaProps>;
  /** Loading state */
  loading?: boolean;
  /** Success state */
  success?: boolean;
  /** Error state */
  error?: boolean;
}
export const AriaEnhancedInput = React.forwardRef<HTMLInputElement, AriaEnhancedInputProps>(
  ({ 
    className, 
    type,
    ariaLabel,
    ariaLabelledBy,
    ariaDescribedBy,
    invalid,
    required,
    errorId,
    helpId,
    ariaProps,
    loading = false,
    success = false,
    error = false,
    disabled,
    ...props 
  }, ref) => {
    // Build describedBy string
    const describedByParts: string[] = [];
    if (helpId) describedByParts.push(helpId);
    if (ariaDescribedBy) describedByParts.push(ariaDescribedBy);
    if (invalid && errorId) describedByParts.push(errorId);
    const finalDescribedBy = describedByParts.length > 0 ? describedByParts.join(' ') : undefined;
    // Create ARIA attributes
    const labelProps = createAriaLabel(ariaLabel, ariaLabelledBy, finalDescribedBy);
    const formProps = createFormAria(invalid, required, finalDescribedBy, errorId);
    // Additional ARIA attributes
    const additionalProps: Partial<AriaProps> = {};
    if (loading) additionalProps['aria-busy'] = true;
    // Merge all ARIA props
    const mergedAriaProps = mergeAriaProps(
      labelProps,
      formProps,
      additionalProps,
      ariaProps
    );
    // Filter out properties that conflict with HTML input attributes
    const finalAriaProps = { ...mergedAriaProps };
    delete finalAriaProps['aria-relevant'];
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 file:border-0 file:bg-transparent file:text-sm file:font-medium",
          {
            'border-destructive focus-visible:ring-destructive': invalid || error,
            'border-green-500 focus-visible:ring-green-500': success,
            'opacity-50 cursor-not-allowed': loading,
          },
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        {...finalAriaProps}
        {...props}
      />
    );
  }
);
AriaEnhancedInput.displayName = "AriaEnhancedInput";
/**
 * Search Input - Specialized input for search functionality
 */
export interface SearchInputProps extends Omit<AriaEnhancedInputProps, 'type' | 'role'> {
  /** Callback when search is performed */
  onSearch?: (value: string) => void;
  /** Whether to show search icon */
  showSearchIcon?: boolean;
  /** Whether to show clear button */
  showClearButton?: boolean;
  /**  */
  placeholder?: string;
}
export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ 
    onSearch,
    showSearchIcon = true,
    showClearButton = true,
    placeholder = "Search...",
    className,
    value,
    onChange,
    ...props 
  }, ref) => {
    const [internalValue, setInternalValue] = React.useState<string>(
      typeof value === 'string' ? value : ''
    );
    const inputRef = React.useRef<HTMLInputElement>(null);
    React.useImperativeHandle<HTMLInputElement | null, HTMLInputElement | null>(
      ref,
      () => inputRef.current,
      []
    );
    React.useEffect(() => {
      if (typeof value === 'string') {
        setInternalValue(value);
      }
    }, [value]);
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInternalValue(newValue);
      onChange?.(e);
    };
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        onSearch?.(internalValue);
      }
    };
    const handleClear = () => {
      setInternalValue('');
      onSearch?.('');
      inputRef.current?.focus();
    };
    const currentValue = typeof value === 'string' ? value : internalValue;
    return (
      <div className="relative">
        {showSearchIcon && (
          <svg
            className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none "
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        )}
        <AriaEnhancedInput
          ref={inputRef}
          type="search"
          role="searchbox"
          placeholder={placeholder}
          value={currentValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          className={cn(
            showSearchIcon && "pl-10",
            showClearButton && currentValue && "pr-10",
            className
          )}
          {...props}
        />
        {showClearButton && currentValue && (
          <Button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground hover:text-foreground focus:text-foreground focus:outline-none "
            aria-label="Clear search"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </Button>
        )}
      </div>
    );
  }
);
SearchInput.displayName = "SearchInput";
/**
 * Password Input - Specialized input for passwords with show/hide toggle
 */
export interface PasswordInputProps extends Omit<AriaEnhancedInputProps, 'type'> {
  /** Whether to show the password toggle button */
  showToggle?: boolean;
}
export const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ showToggle = true, className, ...props }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const inputRef = React.useRef<HTMLInputElement>(null);
    React.useImperativeHandle<HTMLInputElement | null, HTMLInputElement | null>(
      ref,
      () => inputRef.current,
      []
    );
    const togglePasswordVisibility = () => {
      setShowPassword(!showPassword);
      // Keep focus on input after toggle
      setTimeout(() => inputRef.current?.focus(), 0);
    };
    return (
      <div className="relative">
        <AriaEnhancedInput
          ref={inputRef}
          type={showPassword ? "text" : "password"}
          className={cn(
            showToggle && "pr-10",
            className
          )}
          {...props}
        />
        {showToggle && (
          <Button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground hover:text-foreground focus:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded "
            aria-label={showPassword ? "Hide password" : "Show password"}
            aria-pressed={showPassword}
          >
            {showPassword ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"
                />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            )}
          </Button>
        )}
      </div>
    );
  }
);
PasswordInput.displayName = "PasswordInput";
