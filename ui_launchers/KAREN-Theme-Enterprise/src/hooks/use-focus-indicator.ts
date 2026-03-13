import * as React from 'react';

import type { FocusIndicatorProps } from '@/components/ui/focus-indicators';
import { useFocusVisible } from '@/hooks/use-focus-management';

export interface UseFocusIndicatorOptions {
  keyboardOnly?: boolean;
  variant?: FocusIndicatorProps['variant'];
  color?: FocusIndicatorProps['color'];
}

export interface UseFocusIndicatorResult {
  isFocused: boolean;
  shouldShowIndicator: boolean;
  focusProps: {
    onFocus: () => void;
    onBlur: () => void;
  };
  indicatorProps: {
    visible: boolean;
    variant: FocusIndicatorProps['variant'];
    color: FocusIndicatorProps['color'];
  };
}

export function useFocusIndicator({
  keyboardOnly = true,
  variant = 'default',
  color = 'primary',
}: UseFocusIndicatorOptions = {}): UseFocusIndicatorResult {
  const { isFocusVisible } = useFocusVisible();
  const [isFocused, setIsFocused] = React.useState(false);

  const shouldShowIndicator = keyboardOnly ? isFocused && isFocusVisible : isFocused;

  const focusProps = React.useMemo(
    () => ({
      onFocus: () => setIsFocused(true),
      onBlur: () => setIsFocused(false),
    }),
    []
  );

  const indicatorProps = React.useMemo(
    () => ({
      visible: shouldShowIndicator,
      variant,
      color,
    }),
    [color, shouldShowIndicator, variant]
  );

  return {
    isFocused,
    shouldShowIndicator,
    focusProps,
    indicatorProps,
  };
}
