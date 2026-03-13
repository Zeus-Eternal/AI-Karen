/**
 * Input Component - Reusable input component with variants
 */

import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'filled' | 'outlined';
  error?: boolean;
  label?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant = 'default', error = false, label, icon, ...props }, ref) => {
    const baseClasses = 'block w-full rounded-md border-gray-300 shadow-sm placeholder-gray-400 focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:border-gray-600 dark:placeholder-gray-500 dark:focus:ring-blue-500 dark:focus:border-blue-500 dark:bg-gray-700 dark:text-white';
    
    const variantClasses = {
      default: 'border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-700 dark:text-white',
      filled: 'border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-white',
      outlined: 'border-2 border-gray-300 bg-transparent dark:border-gray-600 dark:text-white',
    };

    return (
      <div className="relative">
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
          </label>
        )}
        
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            {icon}
          </div>
        )}
        
        <input
          className={cn(
            baseClasses,
            variantClasses[variant],
            error && 'border-red-500 focus:ring-red-500',
            icon && 'pl-10',
            className
          )}
          ref={ref}
          {...props}
        />
        
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            This field is required
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';