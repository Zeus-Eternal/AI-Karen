import * as React from "react";
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
    ...props
  }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const [isFocused, setIsFocused] = React.useState(false);
    
    const inputType = type === 'password' && showPassword ? 'text' : type;
    
    const handleClear = React.useCallback(() => {
      if (onClear) {
        onClear();
      }
    }, [onClear]);
    
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
          <div className="pl-3 text-muted-foreground pointer-events-none">
            {startIcon}
          </div>
        )}
        
        {/* Input field */}
        <input
          type={inputType}
          className={inputClasses}
          ref={ref}
          disabled={disabled}
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
              tabIndex={-1}
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
              tabIndex={-1}
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
            <div className="text-muted-foreground pointer-events-none">
              {endIcon}
            </div>
          )}
        </div>
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
