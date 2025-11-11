import * as React from 'react';

import FocusIndicator, { type FocusIndicatorProps } from './focus-indicators';

/**
 * Higher-order component helper that wraps the provided component with the FocusIndicator.
 */
export function withFocusIndicator<P extends object, RefType = unknown>(
  Component: React.ForwardRefExoticComponent<P & React.RefAttributes<RefType>>,
  indicatorProps?: Partial<FocusIndicatorProps>
): React.ForwardRefExoticComponent<P & React.RefAttributes<RefType>> {
  const WrappedComponent = React.forwardRef<RefType, P>((props, ref) => (
    <FocusIndicator {...indicatorProps}>
      <Component {...props} ref={ref} />
    </FocusIndicator>
  ));

  const componentName = Component.displayName || Component.name || 'Component';
  WrappedComponent.displayName = `withFocusIndicator(${componentName})`;

  return WrappedComponent;
}
