/**
 * Badge UI Component
 * 
 * Reusable badge component for displaying status indicators and labels.
 */

import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outline' | 'secondary' | 'destructive';
  onClick?: () => void;
  title?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  className = '', 
  variant = 'default',
  onClick,
  title 
}) => {
  const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
  
  const variantClasses = {
    default: 'bg-blue-100 text-blue-800',
    outline: 'border border-gray-300 text-gray-700 bg-white',
    secondary: 'bg-gray-100 text-gray-800',
    destructive: 'bg-red-100 text-red-800',
  };

  const Component = onClick ? 'button' : 'span';

  return (
    <Component 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      onClick={onClick}
      title={title}
    >
      {children}
    </Component>
  );
};