import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';

export interface ProgressiveLoaderProps<T = unknown> {
  children: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'accent';
  text?: string;
  loadData?: (offset: number, limit: number) => Promise<{
    items: T[];
    total: number;
    hasMore: boolean;
  }>;
}

export const ProgressiveLoader: React.FC<ProgressiveLoaderProps> = ({
  children,
  className = '',
  size = 'md',
  color = 'primary',
  text
}) => {
  const [progress, setProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isLoading) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            setIsLoading(false);
            return 100;
          }
          return prev + 10;
        });
      }, 100);

      return () => clearInterval(interval);
    }
    return undefined;
  }, [isLoading]);

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  const colorClasses = {
    primary: 'border-blue-500 text-blue-600',
    secondary: 'border-gray-500 text-gray-600',
    accent: 'border-purple-500 text-purple-600'
  };

  return (
    <div className={cn('flex flex-col items-center justify-center space-y-2', className)}>
      {/* Loader Circle */}
      <div className={cn(
        'rounded-full border-4 border-t-4 animate-spin',
        sizeClasses[size],
        colorClasses[color]
      )} />

      {/* Progress Bar */}
      {isLoading && (
        <div className="w-full max-w-xs">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={cn(
                'bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out',
                color === 'secondary' && 'bg-gray-600',
                color === 'accent' && 'bg-purple-600'
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Text */}
      {text && (
        <p className={cn(
          'text-sm font-medium',
          color === 'secondary' && 'text-gray-600',
          color === 'accent' && 'text-purple-600'
        )}>
          {text}
        </p>
      )}

      {/* Children */}
      {!isLoading && children}
      {isLoading && children}
    </div>
  );
};

export default ProgressiveLoader;
