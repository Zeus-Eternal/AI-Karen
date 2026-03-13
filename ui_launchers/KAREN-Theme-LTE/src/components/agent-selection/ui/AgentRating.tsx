"use client";

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface AgentRatingProps {
  rating: number;
  count?: number;
  showCount?: boolean;
  size?: 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onChange?: (rating: number) => void;
  className?: string;
}

export function AgentRating({
  rating,
  count,
  showCount = false,
  size = 'md',
  interactive = false,
  onChange,
  className,
}: AgentRatingProps) {
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  
  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const handleStarClick = (starValue: number) => {
    if (interactive && onChange) {
      onChange(starValue);
    }
  };

  const handleStarHover = (starValue: number) => {
    if (interactive) {
      setHoverRating(starValue);
    }
  };

  const handleStarLeave = () => {
    if (interactive) {
      setHoverRating(null);
    }
  };

  const renderStar = (starValue: number) => {
    const isFilled = starValue <= (hoverRating !== null ? hoverRating : rating);
    const isHalfFilled = interactive && starValue === Math.ceil(rating) && rating % 1 !== 0 && rating > starValue - 1;
    
    return (
      <button
        type="button"
        className={cn(
          "flex-shrink-0 transition-colors",
          interactive && "cursor-pointer hover:text-yellow-400",
          !interactive && "cursor-default",
          className
        )}
        onClick={() => handleStarClick(starValue)}
        onMouseEnter={() => handleStarHover(starValue)}
        onMouseLeave={handleStarLeave}
        disabled={!interactive}
        aria-label={`${interactive ? 'Rate' : 'Rated'} ${starValue} star${starValue !== 1 ? 's' : ''}`}
      >
        <svg
          className={cn(sizeClasses[size], "text-current")}
          fill="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          {isFilled ? (
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 2.37.67.18.47L12 17.77l-2.37 6.67L5 9.27l6.91-1.01L12 2z" />
          ) : isHalfFilled ? (
            <g>
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 2.37.67.18.47L12 17.77l-2.37 6.67L5 9.27l6.91-1.01L12 2z" opacity="0.5" />
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 2.37.67.18.47L12 17.77l-2.37 6.67L5 9.27l6.91-1.01L12 2z" clipPath="url(#half-star)" />
              <defs>
                <clipPath id="half-star">
                  <rect x="0" y="0" width="12" height="24" />
                </clipPath>
              </defs>
            </g>
          ) : (
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 2.37.67.18.47L12 17.77l-2.37 6.67L5 9.27l6.91-1.01L12 2z" opacity="0.3" />
          )}
        </svg>
      </button>
    );
  };

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <div className="flex items-center">
        {[1, 2, 3, 4, 5].map((starValue) => renderStar(starValue))}
      </div>
      
      {showCount && count !== undefined && (
        <span className={cn(
          "text-sm text-muted-foreground ml-2",
          size === 'sm' && 'text-xs',
          size === 'lg' && 'text-base'
        )}>
          {count > 0 ? `(${count})` : '(0)'}
        </span>
      )}
      
      {!interactive && (
        <span className={cn(
          "text-sm text-muted-foreground ml-2",
          size === 'sm' && 'text-xs',
          size === 'lg' && 'text-base'
        )}>
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  );
}

// Simple rating display (non-interactive)
export function SimpleAgentRating({
  rating,
  count,
  size = 'md',
  className,
}: Omit<AgentRatingProps, 'interactive' | 'onChange'>) {
  return (
    <AgentRating
      rating={rating}
      count={count}
      size={size}
      interactive={false}
      className={className}
    />
  );
}

// Interactive rating component
export function InteractiveAgentRating({
  rating,
  onChange,
  size = 'md',
  className,
}: Pick<AgentRatingProps, 'rating' | 'onChange' | 'size' | 'className'>) {
  return (
    <AgentRating
      rating={rating}
      onChange={onChange}
      size={size}
      interactive={true}
      className={className}
    />
  );
}