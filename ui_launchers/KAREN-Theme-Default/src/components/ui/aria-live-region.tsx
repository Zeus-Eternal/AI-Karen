/**
 * ARIA Live Region Component
 * Provides screen reader announcements for dynamic content changes
 */

import React, { useEffect, useRef, useState } from 'react';
import { createAriaLive, generateAriaId } from '@/utils/aria';
import { cn } from '@/lib/utils';

export interface AriaLiveRegionProps {
  /** The live region politeness level */
  politeness?: 'off' | 'polite' | 'assertive';
  /** Whether the entire region should be announced when any part changes */
  atomic?: boolean;
  /** What types of changes should be announced */
  relevant?: 'additions' | 'removals' | 'text' | 'all' | 'additions text' | 'additions removals' | 'text removals' | 'additions text removals';
  /** Custom className for styling */
  className?: string;
  /** Children to render in the live region */
  children?: React.ReactNode;
  /** ID for the live region */
  id?: string;
}

/**
 * AriaLiveRegion - A component for creating accessible live regions
 */
export const AriaLiveRegion = React.forwardRef<HTMLDivElement, AriaLiveRegionProps>(
  ({ 
    politeness = 'polite', 
    atomic = false, 
    relevant = 'additions text',
    className,
    children,
    id,
    ...props 
  }, ref) => {
    const generatedId = useRef(id || generateAriaId('live-region'));
    const ariaPropsRaw = createAriaLive(politeness, atomic, relevant);
    
    // Filter out properties that conflict with HTML div attributes
    const { 'aria-relevant': ariaRelevant, ...safeAriaProps } = ariaPropsRaw;
    
    // Create safe aria-relevant value for HTML
    const htmlAriaRelevant = ariaRelevant === 'additions text removals' ? 'all' : 
                            ariaRelevant === 'additions text' ? 'additions text' as const :
                            ariaRelevant;

    return (
      <div
        ref={ref}
        id={generatedId.current}
        className={cn(
          // Visually hidden but accessible to screen readers
          'sr-only',
          className
        )}
        {...safeAriaProps}
        aria-relevant={htmlAriaRelevant}
        {...props}
      >
        {children}
      </div>
    );
  }
);

AriaLiveRegion.displayName = 'AriaLiveRegion';

/**
 * Hook for managing live announcements
 */
export interface UseAriaAnnouncementsOptions {
  /** Default politeness level for announcements */
  defaultPoliteness?: 'polite' | 'assertive';
  /** Delay before clearing announcements (in ms) */
  clearDelay?: number;
}

export const useAriaAnnouncements = (options: UseAriaAnnouncementsOptions = {}) => {
  const { defaultPoliteness = 'polite', clearDelay = 1000 } = options;
  const [politeMessage, setPoliteMessage] = useState('');
  const [assertiveMessage, setAssertiveMessage] = useState('');
  const politeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const assertiveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const announce = (
    message: string, 
    politeness: 'polite' | 'assertive' = defaultPoliteness
  ) => {
    if (politeness === 'assertive') {
      // Clear any existing timeout
      if (assertiveTimeoutRef.current) {
        clearTimeout(assertiveTimeoutRef.current);
      }
      
      setAssertiveMessage(message);
      
      // Clear the message after delay
      assertiveTimeoutRef.current = setTimeout(() => {
        setAssertiveMessage('');
      }, clearDelay);
    } else {
      // Clear any existing timeout
      if (politeTimeoutRef.current) {
        clearTimeout(politeTimeoutRef.current);
      }
      
      setPoliteMessage(message);
      
      // Clear the message after delay
      politeTimeoutRef.current = setTimeout(() => {
        setPoliteMessage('');
      }, clearDelay);
    }
  };

  const clearAnnouncements = () => {
    setPoliteMessage('');
    setAssertiveMessage('');
    if (politeTimeoutRef.current) clearTimeout(politeTimeoutRef.current);
    if (assertiveTimeoutRef.current) clearTimeout(assertiveTimeoutRef.current);
  };

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (politeTimeoutRef.current) clearTimeout(politeTimeoutRef.current);
      if (assertiveTimeoutRef.current) clearTimeout(assertiveTimeoutRef.current);
    };
  }, []);

  return {
    announce,
    clearAnnouncements,
    politeMessage,
    assertiveMessage,
  };
};

/**
 * AriaAnnouncer - A component that provides announcement functionality
 */
export interface AriaAnnouncerProps {
  children: (announce: (message: string, politeness?: 'polite' | 'assertive') => void) => React.ReactNode;
}

export const AriaAnnouncer: React.FC<AriaAnnouncerProps> = ({ children }) => {
  const { announce, politeMessage, assertiveMessage } = useAriaAnnouncements();

  return (
    <>
      {children(announce)}
      <AriaLiveRegion politeness="polite">
        {politeMessage}
      </AriaLiveRegion>
      <AriaLiveRegion politeness="assertive">
        {assertiveMessage}
      </AriaLiveRegion>
    </>
  );
};

/**
 * Status announcement component for loading states
 */
export interface AriaStatusProps {
  /** The status message to announce */
  message: string;
  /** Whether this is a loading state */
  loading?: boolean;
  /** Whether this is an error state */
  error?: boolean;
  /** Whether this is a success state */
  success?: boolean;
  /** Custom className */
  className?: string;
}

export const AriaStatus: React.FC<AriaStatusProps> = ({
  message,
  loading = false,
  error = false,
  success = false,
  className,
}) => {
  const politeness = error ? 'assertive' : 'polite';
  const role = error ? 'alert' : 'status';

  return (
    <div
      role={role}
      aria-live={politeness}
      aria-atomic="true"
      className={cn('sr-only', className)}
    >
      {loading && 'Loading: '}
      {error && 'Error: '}
      {success && 'Success: '}
      {message}
    </div>
  );
};

/**
 * Progress announcement component
 */
export interface AriaProgressProps {
  /** Current progress value */
  value: number;
  /** Maximum progress value */
  max?: number;
  /** Minimum progress value */
  min?: number;
  /** Label for the progress */
  label?: string;
  /** Whether to announce progress changes */
  announceChanges?: boolean;
  /** Custom className */
  className?: string;
}

export const AriaProgress: React.FC<AriaProgressProps> = ({
  value,
  max = 100,
  min = 0,
  label,
  announceChanges = true,
  className,
}) => {
  const [lastAnnouncedValue, setLastAnnouncedValue] = useState(value);
  const { announce } = useAriaAnnouncements();

  const percentage = Math.round(((value - min) / (max - min)) * 100);

  useEffect(() => {
    if (announceChanges && Math.abs(value - lastAnnouncedValue) >= 10) {
      announce(`${label ? `${label}: ` : ''}${percentage}% complete`);
      setLastAnnouncedValue(value);
    }
  }, [value, lastAnnouncedValue, percentage, label, announce, announceChanges]);

  return (
    <div
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={min}
      aria-valuemax={max}
      aria-label={label}
      className={cn('sr-only', className)}
    >
      {label && `${label}: `}{percentage}% complete
    </div>
  );
};

export default AriaLiveRegion;