"use client";

import React from "react";
import { useFocusTrap } from "../../hooks/use-focus-management";

interface FocusTrapProps {
  children: React.ReactNode;
  enabled?: boolean;
  /** CSS selector string or HTMLElement to receive initial focus when trap activates */
  initialFocus?: string | HTMLElement | null;
  /** When true, focus returns to the previously focused element on unmount/deactivate */
  restoreFocus?: boolean;
  className?: string;
}

/**
 * FocusTrap
 * Wrap content to confine keyboard focus within the region when `enabled` is true.
 * Delegates core trapping logic to `useFocusTrap` (portal/modals/sheets ready).
 */
export function FocusTrap({
  children,
  enabled = true,
  initialFocus = null,
  restoreFocus = true,
  className,
}: FocusTrapProps) {
  const { containerProps, isActive } = useFocusTrap<HTMLDivElement>(enabled, {
    initialFocus,
    restoreFocus,
  });

  return (
    <div
      {...containerProps}
      className={className}
      data-focus-trap={enabled ? "true" : "false"}
      data-focus-active={isActive ? "true" : "false"}
    >
      {children}
    </div>
  );
}

export default FocusTrap;
