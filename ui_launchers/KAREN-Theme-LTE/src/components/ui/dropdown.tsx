/**
 * Dropdown Component - Reusable dropdown component
 */

import React, { useState, useRef, useEffect, ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface DropdownItem {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
  disabled?: boolean;
  variant?: 'default' | 'destructive';
}

export interface DropdownProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  items: DropdownItem[];
  trigger?: React.ReactNode;
  className?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  items,
  trigger,
  className = '',
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isOpen]);

  const handleTriggerClick = () => {
    setIsOpen(!isOpen);
  };

  const handleItemClick = (item: DropdownItem) => {
    item.onClick();
    setIsOpen(false);
  };

  return (
    <div className="relative inline-block text-left">
      <button
        ref={triggerRef}
        onClick={handleTriggerClick}
        className={cn(
          'inline-flex justify-center w-full rounded-md border border-gray-300 shadow-sm px-4 py-2 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
          className
        )}
        {...props}
      >
        {trigger || 'Options'}
        <svg className="-mr-1 ml-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.707 0l2.586 2.586a1 1 0 001.414 1.414L10 14.586a1 1 0 001.414-1.414 2.586-2.586a1 1 0 01-1.414-1.414L5.293 7.293a1 1 0 01-1.707-.293z" clipRule="evenodd" />
        </svg>
      </button>
      
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
          role="menu"
          aria-orientation="vertical"
        >
          <div className="py-1">
            {items.map((item, index) => (
              <button
                key={index}
                onClick={() => handleItemClick(item)}
                disabled={item.disabled}
                className={cn(
                  'block w-full text-left px-4 py-2 text-sm',
                  item.variant === 'destructive'
                    ? 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800',
                  item.disabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                {item.icon && (
                  <span className="mr-3 h-5 w-5 inline-block">
                    {item.icon}
                  </span>
                )}
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
