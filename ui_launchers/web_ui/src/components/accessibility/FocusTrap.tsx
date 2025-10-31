'use client';

import React, { useEffect, useRef } from 'react';
import { useFocusTrap } from '../../hooks/use-focus-management';

interface FocusTrapProps {
  children: React.ReactNode;
  enabled?: boolean;
  initialFocus?: string | HTMLElement | null;
  restoreFocus?: boolean;
  className?: string;
}

export function FocusTrap({
  children,
  enabled = true,
  initialFocus,
  restoreFocus = true,
  className,
}: FocusTrapProps) {
  const {
    containerProps,
    isActive,
  } = useFocusTrap(enabled, {
    initialFocus,
    restoreFocus,
  });

  return (
    <div
      {...containerProps}
      className={className}
      data-focus-trap={enabled}
      data-focus-active={isActive}
    >
      {children}
    </div>
  );
}

export default FocusTrap;