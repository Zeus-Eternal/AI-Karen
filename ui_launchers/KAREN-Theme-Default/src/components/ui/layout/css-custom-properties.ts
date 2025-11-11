import type { CSSProperties } from "react";

export type CSSCustomPropertyStyles = CSSProperties & {
  [customProperty: `--${string}`]: string | number | undefined;
};
