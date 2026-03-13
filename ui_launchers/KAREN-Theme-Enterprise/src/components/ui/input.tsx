import React from "react";
const { forwardRef, useState, useCallback } = React;
import { Eye, EyeOff, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import type { InputProps } from './input-types';

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({
    className,
    type = "text",
    disabled,
    error,
    startIcon,
    endIcon,
    clearable,
    onClear,
    showPasswordToggle = false,
    ariaLabel,
    ariaDescribedBy,
    required = false,
    ...props
  }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const [isFocused, setIsFocused] = React.useState(false);
    
    const inputType = type === 'password' && showPassword ? 'text' : type;
    
    const handleClear = useCallback(() => {
      if (onClear) {
        onClear();
      }
    }, [onClear]);
    
    const inputId = React.useId();
    const describedBy = [
      error ? `${inputId}-error` : null,
      ariaDescribedBy
    ].filter(Boolean).join(' ') || undefined;
    
    const containerClasses = cn(
      "flex items-center w-full rounded-md border transition-all duration-200",
      "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2",
      disabled && "opacity-50 cursor-not-allowed",
      error
        ? "border-destructive focus-within:ring-destructive"
        : "border-input focus-within:ring-primary",
      isFocused && "shadow-sm",
      className
    );
    
    const inputClasses = cn(
      "flex-1 w-full bg-transparent py-2 text-sm ring-offset-background",
      "placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed",
      startIcon ? "pl-10 pr-3" : "pl-3",
      (endIcon || clearable || showPasswordToggle) ? "pr-10" : "pr-3",
      className
    );
    
    return (
      <div className={containerClasses}>
        {/* Start icon */}
        {startIcon && (
          <div className="pl-3 text-muted-foreground pointer-events-none" aria-hidden="true">
            {startIcon}
          </div>
        )}
        
        {/* Input field */}
        <input
          id={inputId}
          type={inputType}
          className={inputClasses}
          ref={ref}
          disabled={disabled}
          required={required}
          aria-label={ariaLabel}
          aria-describedby={describedBy}
          aria-invalid={!!error}
          aria-required={required}
          onFocus={(e) => {
            setIsFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            props.onBlur?.(e);
          }}
          {...props}
        />
        
        {/* End section */}
        <div className="absolute right-3 flex items-center gap-1">
          {/* Clear button */}
          {clearable && props.value && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-5 w-5 opacity-70 hover:opacity-100"
              onClick={handleClear}
              disabled={disabled}
              aria-label="Clear input"
              tabIndex={disabled ? -1 : 0}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
          
          {/* Password toggle */}
          {type === 'password' && showPasswordToggle && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-5 w-5 opacity-70 hover:opacity-100"
              onClick={() => setShowPassword(!showPassword)}
              disabled={disabled}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={disabled ? -1 : 0}
            >
              {showPassword ? (
                <EyeOff className="h-3 w-3" />
              ) : (
                <Eye className="h-3 w-3" />
              )}
            </Button>
          )}
          
          {/* End icon */}
          {endIcon && (
            <div className="text-muted-foreground pointer-events-none" aria-hidden="true">
              {endIcon}
            </div>
          )}
        </div>
        
        {/* Error message */}
        {error && (
          <div id={`${inputId}-error`} className="sr-only" role="alert">
            Input has an error
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
