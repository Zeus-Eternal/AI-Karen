import * as React from 'react';

import FocusIndicator, { type FocusIndicatorProps } from './focus-indicators';

/**
 * Higher-order component helper that wraps the provided component with the FocusIndicator.
 */
export function withFocusIndicator(
  Component: React.ComponentType<any>,
  indicatorProps?: Partial<FocusIndicatorProps>
) {
  const WrappedComponent = React.forwardRef<any, any>((props, ref) => (
    <FocusIndicator {...indicatorProps}>
      <Component {...props} ref={ref} />
    </FocusIndicator>
  ));

  const componentName = Component.displayName || Component.name || 'Component';
  WrappedComponent.displayName = `withFocusIndicator(${componentName})`;

  return WrappedComponent as React.ComponentType<any>;
}
