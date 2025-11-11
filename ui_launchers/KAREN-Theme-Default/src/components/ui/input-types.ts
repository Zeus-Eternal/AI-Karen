import type * as React from "react";

/**
 * Shared props for the core input component.
 * Keeping this in a dedicated module avoids mixing non-component exports with the provider
 * while still allowing other modules to extend or reuse the base props.
 */
export type InputProps = React.ComponentProps<"input">;
