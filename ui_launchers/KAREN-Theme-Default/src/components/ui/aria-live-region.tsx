/**
 * ARIA Live Region Component
 * Provides screen reader announcements for dynamic content changes
 */

import React, { useEffect, useMemo, useRef } from 'react';
import { createAriaLive, generateAriaId, type AriaRelevant } from '@/utils/aria';
import { cn } from '@/lib/utils';
import { useAriaAnnouncements } from './aria-live-announcements';

// eslint-disable-next-line react-refresh/only-export-components
export interface AriaLiveRegionProps {
  /** The live region politeness level */
  politeness?: 'off' | 'polite' | 'assertive';
  /** Whether the entire region should be announced when any part changes */
  atomic?: boolean;
  /** What types of changes should be announced */
  relevant?: AriaRelevant;
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
    const generatedId = useMemo(
      () => id ?? generateAriaId('live-region'),
      [id]
    );
    const ariaPropsRaw = createAriaLive(politeness, atomic, relevant);

    // Filter out properties that conflict with HTML div attributes
    const { 'aria-relevant': ariaRelevant, ...safeAriaProps } = ariaPropsRaw;

    return (
      <div
        ref={ref}
        id={generatedId}
        className={cn(
          // Visually hidden but accessible to screen readers
          'sr-only',
          className
        )}
        {...safeAriaProps}
        aria-relevant={ariaRelevant}
        {...props}
      >
        {children}
      </div>
    );
  }
);

AriaLiveRegion.displayName = 'AriaLiveRegion';

/**
 * AriaAnnouncer - A component that provides announcement functionality
 */
// eslint-disable-next-line react-refresh/only-export-components
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
// eslint-disable-next-line react-refresh/only-export-components
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
  const lastAnnouncedValueRef = useRef(value);
  const { announce } = useAriaAnnouncements();

  const range = max - min;
  const safeRange = range === 0 ? 1 : range;
  const percentage = Math.round(((value - min) / safeRange) * 100);

  useEffect(() => {
    if (!announceChanges) {
      return;
    }

    const lastValue = lastAnnouncedValueRef.current;

    if (Math.abs(value - lastValue) >= 10) {
      announce(`${label ? `${label}: ` : ''}${percentage}% complete`);
      lastAnnouncedValueRef.current = value;
    }
  }, [value, percentage, label, announce, announceChanges]);

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