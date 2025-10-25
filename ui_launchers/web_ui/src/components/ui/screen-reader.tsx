/**
 * Screen Reader Support Components
 * Provides comprehensive screen reader support and announcements
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useAriaAnnouncements, AriaLiveRegion } from './aria-live-region';

/**
 * ScreenReaderOnly - Content visible only to screen readers
 */
export interface ScreenReaderOnlyProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Content to show only to screen readers */
  children: React.ReactNode;
  /** Whether to use a div instead of span */
  asDiv?: boolean;
}

export const ScreenReaderOnly = React.forwardRef<HTMLElement, ScreenReaderOnlyProps>(
  ({ children, asDiv = false, className, ...props }, ref) => {
    const Component = asDiv ? 'div' : 'span';
    
    return (
      <Component
        ref={ref as any}
        className={cn('sr-only', className)}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

ScreenReaderOnly.displayName = 'ScreenReaderOnly';

/**
 * VisuallyHidden - Alias for ScreenReaderOnly
 */
export const VisuallyHidden = ScreenReaderOnly;

/**
 * ScreenReaderAnnouncer - Global announcer for screen reader messages
 */
export interface ScreenReaderAnnouncerProps {
  /** Children that can trigger announcements */
  children: (announce: (message: string, priority?: 'polite' | 'assertive') => void) => React.ReactNode;
}

export const ScreenReaderAnnouncer: React.FC<ScreenReaderAnnouncerProps> = ({ children }) => {
  const { announce, politeMessage, assertiveMessage } = useAriaAnnouncements();

  return (
    <>
      {children(announce)}
      <AriaLiveRegion politeness="polite" id="polite-announcer">
        {politeMessage}
      </AriaLiveRegion>
      <AriaLiveRegion politeness="assertive" id="assertive-announcer">
        {assertiveMessage}
      </AriaLiveRegion>
    </>
  );
};

/**
 * DescriptiveText - Provides descriptive text for complex interactions
 */
export interface DescriptiveTextProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** The descriptive text */
  description: string;
  /** Whether to show the description visually */
  visuallyHidden?: boolean;
  /** ID for the description (for aria-describedby) */
  descriptionId?: string;
}

export const DescriptiveText = React.forwardRef<HTMLSpanElement, DescriptiveTextProps>(
  ({ 
    description, 
    visuallyHidden = true, 
    descriptionId,
    className, 
    ...props 
  }, ref) => {
    const id = descriptionId || React.useId();

    return (
      <span
        ref={ref}
        id={id}
        className={cn(
          visuallyHidden && 'sr-only',
          'description-text',
          className
        )}
        {...props}
      >
        {description}
      </span>
    );
  }
);

DescriptiveText.displayName = 'DescriptiveText';

/**
 * HeadingStructure - Ensures proper heading hierarchy
 */
export interface HeadingStructureProps extends React.HTMLAttributes<HTMLHeadingElement> {
  /** Heading level (1-6) */
  level: 1 | 2 | 3 | 4 | 5 | 6;
  /** Visual level (can be different from semantic level) */
  visualLevel?: 1 | 2 | 3 | 4 | 5 | 6;
  /** Heading text */
  children: React.ReactNode;
}

export const HeadingStructure = React.forwardRef<HTMLHeadingElement, HeadingStructureProps>(
  ({ level, visualLevel, className, children, ...props }, ref) => {
    const visualClass = visualLevel ? `text-${visualLevel === 1 ? '4xl' : visualLevel === 2 ? '3xl' : visualLevel === 3 ? '2xl' : visualLevel === 4 ? 'xl' : visualLevel === 5 ? 'lg' : 'base'}` : '';

    const commonProps = {
      ref: ref as any,
      className: cn(
        'heading-structure font-semibold',
        visualClass,
        className
      ),
      ...props
    };

    switch (level) {
      case 1:
        return <h1 {...commonProps}>{children}</h1>;
      case 2:
        return <h2 {...commonProps}>{children}</h2>;
      case 3:
        return <h3 {...commonProps}>{children}</h3>;
      case 4:
        return <h4 {...commonProps}>{children}</h4>;
      case 5:
        return <h5 {...commonProps}>{children}</h5>;
      case 6:
        return <h6 {...commonProps}>{children}</h6>;
      default:
        return <h1 {...commonProps}>{children}</h1>;
    }
  }
);

HeadingStructure.displayName = 'HeadingStructure';

/**
 * LandmarkRegion - Creates semantic landmark regions
 */
export interface LandmarkRegionProps extends React.HTMLAttributes<HTMLElement> {
  /** Type of landmark */
  landmark: 'banner' | 'main' | 'navigation' | 'complementary' | 'contentinfo' | 'search' | 'region';
  /** Accessible label for the landmark */
  label?: string;
  /** ID of element that labels this landmark */
  labelledBy?: string;
  /** Children content */
  children: React.ReactNode;
}

export const LandmarkRegion = React.forwardRef<HTMLElement, LandmarkRegionProps>(
  ({ landmark, label, labelledBy, className, children, ...props }, ref) => {
    const getElement = () => {
      switch (landmark) {
        case 'banner':
          return 'header';
        case 'main':
          return 'main';
        case 'navigation':
          return 'nav';
        case 'complementary':
          return 'aside';
        case 'contentinfo':
          return 'footer';
        default:
          return 'section';
      }
    };

    const Element = getElement();

    return (
      <Element
        ref={ref as any}
        role={landmark === 'region' ? 'region' : undefined}
        aria-label={label}
        aria-labelledby={labelledBy}
        className={cn('landmark-region', className)}
        {...props}
      >
        {children}
      </Element>
    );
  }
);

LandmarkRegion.displayName = 'LandmarkRegion';

/**
 * StatusMessage - Announces status changes to screen readers
 */
export interface StatusMessageProps {
  /** The status message */
  message: string;
  /** Type of status */
  type?: 'info' | 'success' | 'warning' | 'error';
  /** Whether to announce immediately */
  announce?: boolean;
  /** Custom className */
  className?: string;
}

export const StatusMessage: React.FC<StatusMessageProps> = ({
  message,
  type = 'info',
  announce = true,
  className,
}) => {
  const role = type === 'error' ? 'alert' : 'status';
  const politeness = type === 'error' ? 'assertive' : 'polite';

  return (
    <div
      role={role}
      aria-live={announce ? politeness : undefined}
      aria-atomic="true"
      className={cn('sr-only', className)}
    >
      {type !== 'info' && `${type.charAt(0).toUpperCase() + type.slice(1)}: `}
      {message}
    </div>
  );
};

/**
 * LoadingAnnouncement - Announces loading states
 */
export interface LoadingAnnouncementProps {
  /** Whether currently loading */
  loading: boolean;
  /** Loading message */
  loadingMessage?: string;
  /** Completion message */
  completionMessage?: string;
  /** Error message */
  errorMessage?: string;
  /** Current error state */
  error?: boolean;
}

export const LoadingAnnouncement: React.FC<LoadingAnnouncementProps> = ({
  loading,
  loadingMessage = 'Loading...',
  completionMessage = 'Loading complete',
  errorMessage = 'Loading failed',
  error = false,
}) => {
  const [previousLoading, setPreviousLoading] = React.useState(loading);
  const [shouldShowCompletion, setShouldShowCompletion] = React.useState(false);

  React.useEffect(() => {
    // Announce completion when loading changes from true to false
    if (previousLoading && !loading && !error) {
      setShouldShowCompletion(true);
      // Clear the completion message after a short delay
      const timer = setTimeout(() => setShouldShowCompletion(false), 100);
      return () => clearTimeout(timer);
    }
    setPreviousLoading(loading);
  }, [loading, previousLoading, error]);

  const shouldAnnounceError = error;

  return (
    <>
      {loading && (
        <StatusMessage 
          message={loadingMessage} 
          type="info"
          announce={true}
        />
      )}
      {shouldShowCompletion && (
        <StatusMessage 
          message={completionMessage} 
          type="success"
          announce={true}
        />
      )}
      {shouldAnnounceError && (
        <StatusMessage 
          message={errorMessage} 
          type="error"
          announce={true}
        />
      )}
    </>
  );
};

/**
 * InteractionDescription - Describes complex interactions
 */
export interface InteractionDescriptionProps {
  /** Description of the interaction */
  description: string;
  /** Keyboard shortcuts */
  shortcuts?: string[];
  /** Additional instructions */
  instructions?: string[];
  /** ID for the description */
  id?: string;
}

export const InteractionDescription: React.FC<InteractionDescriptionProps> = ({
  description,
  shortcuts = [],
  instructions = [],
  id,
}) => {
  const descriptionId = id || React.useId();

  return (
    <div id={descriptionId} className="sr-only">
      <p>{description}</p>
      {shortcuts.length > 0 && (
        <div>
          <p>Keyboard shortcuts:</p>
          <ul>
            {shortcuts.map((shortcut, index) => (
              <li key={index}>{shortcut}</li>
            ))}
          </ul>
        </div>
      )}
      {instructions.length > 0 && (
        <div>
          <p>Instructions:</p>
          <ul>
            {instructions.map((instruction, index) => (
              <li key={index}>{instruction}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

/**
 * Hook for managing screen reader announcements
 */
export const useScreenReaderAnnouncements = () => {
  const { announce } = useAriaAnnouncements();

  const announceNavigation = React.useCallback((destination: string) => {
    announce(`Navigated to ${destination}`, 'polite');
  }, [announce]);

  const announceAction = React.useCallback((action: string) => {
    announce(`${action} completed`, 'polite');
  }, [announce]);

  const announceError = React.useCallback((error: string) => {
    announce(`Error: ${error}`, 'assertive');
  }, [announce]);

  const announceSuccess = React.useCallback((message: string) => {
    announce(`Success: ${message}`, 'polite');
  }, [announce]);

  const announceLoading = React.useCallback((message: string = 'Loading') => {
    announce(message, 'polite');
  }, [announce]);

  return {
    announce,
    announceNavigation,
    announceAction,
    announceError,
    announceSuccess,
    announceLoading,
  };
};

/**
 * ScreenReaderTestHelper - Component for testing screen reader functionality
 */
export const ScreenReaderTestHelper: React.FC<{
  onTest?: (message: string) => void;
}> = ({ onTest }) => {
  const { announce } = useScreenReaderAnnouncements();

  const testAnnouncements = () => {
    announce('Screen reader test: polite announcement', 'polite');
    setTimeout(() => {
      announce('Screen reader test: assertive announcement', 'assertive');
    }, 1000);
    onTest?.('Screen reader test completed');
  };

  return (
    <div className="sr-only">
      <button onClick={testAnnouncements}>
        Test Screen Reader Announcements
      </button>
    </div>
  );
};

export default ScreenReaderOnly;