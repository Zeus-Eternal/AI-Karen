import type { CSSCustomPropertyStyles } from './css-custom-properties';

export function assignResponsiveProperties(
  target: CSSCustomPropertyStyles,
  responsiveValues: Record<`--${string}`, string>
): void {
  const keys = Object.keys(responsiveValues) as Array<`--${string}`>;

  keys.forEach(key => {
    const value = responsiveValues[key];
    if (value !== undefined) {
      target[key] = value;
    }
  });
}
