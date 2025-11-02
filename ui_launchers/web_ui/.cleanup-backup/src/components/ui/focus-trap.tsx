/**
 * Focus Trap Component
 * Provides focus trapping functionality for modals, dialogs, and other overlay components
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { useFocusTrap } from '@/hooks/use-focus-management';

export interface FocusTrapProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether the focus trap is active */
  active: boolean;
  /** Initial element to focus (selector or element) */
  initialFocus?: string | HTMLElement | null;
  /** Fallback element to focus if initialFocus is not found */
  fallbackFocus?: string | HTMLElement | null;
  /** Whether to restore focus when trap becomes inactive */
  restoreFocus?: boolean;
  /** Elements to exclude from focus trap (selectors) */
  excludeFromTrap?: string[];
  /** Callback when focus enters the trap */
  onFocusEnter?: () => void;
  /** Callback when focus leaves the trap */
  onFocusLeave?: () => void;
  /** Children to render within the focus trap */
  children: React.ReactNode;
}

/**
 * FocusTrap - Traps focus within its children when active
 */
export const FocusTrap = React.forwardRef<HTMLDivElement, FocusTrapProps>(
  ({
    active,
    initialFocus,
    fallbackFocus,
    restoreFocus = true,
    excludeFromTrap,
    onFocusEnter,
    onFocusLeave,
    className,
    children,
    ...props
  }, ref) => {
    const focusTrap = useFocusTrap(active, {
      initialFocus,
      fallbackFocus,
      restoreFocus,
      excludeFromTrap,
      onFocusEnter,
      onFocusLeave,
    });

    // Merge refs - combine the external ref with the focus trap's container ref
    const mergedRef = React.useCallback((node: HTMLDivElement | null) => {
      // Set the focus trap's container ref
      if (focusTrap.containerRef && 'current' in focusTrap.containerRef) {
        (focusTrap.containerRef as React.MutableRefObject<HTMLDivElement | null>).current = node;
      }
      
      // Set the external ref
      if (typeof ref === 'function') {
        ref(node);
      } else if (ref && 'current' in ref) {
        (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
      }
    }, [focusTrap.containerRef, ref]);

    // Extract ref from containerProps to avoid duplication
    const { ref: _, ...containerPropsWithoutRef } = focusTrap.containerProps;

    return (
      <div
        ref={mergedRef}
        className={cn('focus-trap', className)}
        {...containerPropsWithoutRef}
        {...props}
      >
        {children}
      </div>
    );
  }
);

FocusTrap.displayName = 'FocusTrap';

/**
 * ModalFocusTrap - Specialized focus trap for modal dialogs
 */
export interface ModalFocusTrapProps extends Omit<FocusTrapProps, 'active' | 'initialFocus'> {
  /** Whether the modal is open */
  open: boolean;
  /** Auto-focus the first interactive element */
  autoFocus?: boolean;
}

export const ModalFocusTrap = React.forwardRef<HTMLDivElement, ModalFocusTrapProps>(
  ({
    open,
    autoFocus = true,
    className,
    children,
    ...props
  }, ref) => {
    const initialFocus = autoFocus ? 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])' : null;

    return (
      <FocusTrap
        ref={ref}
        active={open}
        initialFocus={initialFocus}
        className={cn('modal-focus-trap', className)}
        {...props}
      >
        {children}
      </FocusTrap>
    );
  }
);

ModalFocusTrap.displayName = 'ModalFocusTrap';

/**
 * FocusGuard - Invisible elements that help manage focus flow
 */
export const FocusGuard: React.FC<{
  onFocus?: () => void;
  'data-testid'?: string;
}> = ({ onFocus, ...props }) => {
  return (
    <div
      tabIndex={0}
      style={{
        position: 'fixed',
        top: 1,
        left: 1,
        width: 1,
        height: 0,
        padding: 0,
        margin: -1,
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: 0,
      }}
      onFocus={onFocus}
      {...props}
    />
  );
};

/**
 * FocusTrapWithGuards - Focus trap with guard elements for better focus management
 */
export interface FocusTrapWithGuardsProps extends FocusTrapProps {
  /** Whether to include focus guards */
  includeGuards?: boolean;
}

export const FocusTrapWithGuards = React.forwardRef<HTMLDivElement, FocusTrapWithGuardsProps>(
  ({
    includeGuards = true,
    children,
    ...props
  }, ref) => {
    const focusTrap = useFocusTrap(props.active);

    const handleTopGuardFocus = React.useCallback(() => {
      focusTrap.focusLast();
    }, [focusTrap]);

    const handleBottomGuardFocus = React.useCallback(() => {
      focusTrap.focusFirst();
    }, [focusTrap]);

    return (
      <>
        {includeGuards && props.active && (
          <FocusGuard 
            onFocus={handleTopGuardFocus}
            data-testid="focus-guard-top"
          />
        )}
        <FocusTrap ref={ref} {...props}>
          {children}
        </FocusTrap>
        {includeGuards && props.active && (
          <FocusGuard 
            onFocus={handleBottomGuardFocus}
            data-testid="focus-guard-bottom"
          />
        )}
      </>
    );
  }
);

FocusTrapWithGuards.displayName = 'FocusTrapWithGuards';

export default FocusTrap;