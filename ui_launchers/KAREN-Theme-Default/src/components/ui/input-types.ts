import type * as React from "react";

/**
 * Shared props for the core input component.
 * Keeping this in a dedicated module avoids mixing non-component exports with the provider
 * while still allowing other modules to extend or reuse the base props.
 */
export interface InputProps extends Omit<React.ComponentProps<"input">, "ref"> {
  error?: boolean;
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
  clearable?: boolean;
  onClear?: () => void;
  showPasswordToggle?: boolean;
}
