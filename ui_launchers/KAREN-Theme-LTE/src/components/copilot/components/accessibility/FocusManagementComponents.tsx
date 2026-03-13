import React from 'react';
import { 
  addVisibleFocusIndicators, 
  removeVisibleFocusIndicators,
  useFocusTrap,
  useFocusRestore
} from '../../utils/focus-management';

/**
 * Component that adds visible focus indicators to the document
 */
export const FocusIndicatorProvider: React.FC = () => {
  React.useEffect(() => {
    addVisibleFocusIndicators();
    
    return () => {
      removeVisibleFocusIndicators();
    };
  }, []);
  
  return null;
};

/**
 * Skip to main content link component
 */
export const SkipToMainContent: React.FC = () => {
  const handleSkip = (e: React.MouseEvent) => {
    e.preventDefault();
    const mainElement = document.querySelector('main, [role="main"]');
    if (mainElement) {
      (mainElement as HTMLElement).focus();
      mainElement.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  return (
    <a
      href="#main-content"
      onClick={handleSkip}
      className="skip-to-main-content"
      style={{
        position: 'absolute',
        top: '-40px',
        left: '0',
        background: 'var(--copilot-color-primary, #3b82f6)',
        color: 'white',
        padding: '8px',
        textDecoration: 'none',
        borderRadius: '0 0 4px 0',
        zIndex: 9999,
        transition: 'top 0.3s ease'
      }}
      onFocus={(e) => {
        e.currentTarget.style.top = '0';
      }}
      onBlur={(e) => {
        e.currentTarget.style.top = '-40px';
      }}
    >
      Skip to main content
    </a>
  );
};

/**
 * Focus trap container component
 */
export const FocusTrapContainer: React.FC<{
  isActive: boolean;
  children: React.ReactNode;
  className?: string;
  initialFocus?: React.RefObject<HTMLDivElement>;
  returnFocus?: React.RefObject<HTMLDivElement>;
  escapeDeactivates?: boolean;
  clickOutsideDeactivates?: boolean;
  onDeactivate?: () => void;
}> = ({
  isActive,
  children,
  className = '',
  initialFocus,
  returnFocus,
  escapeDeactivates = true,
  clickOutsideDeactivates = false,
  onDeactivate
}) => {
  const { containerRef } = useFocusTrap(isActive, {
    initialFocus: initialFocus?.current,
    returnFocus: returnFocus?.current,
    escapeDeactivates,
    clickOutsideDeactivates,
    onDeactivate
  });
  
  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  );
};

/**
 * Focus restoration component
 */
export const FocusRestorer: React.FC<{
  isActive: boolean;
  children: React.ReactNode;
}> = ({ isActive, children }) => {
  useFocusRestore(isActive);
  
  return <>{children}</>;
};

export default FocusIndicatorProvider;