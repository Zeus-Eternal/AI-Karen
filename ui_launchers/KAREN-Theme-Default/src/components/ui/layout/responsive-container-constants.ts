export const defaultContainerBreakpoints = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

export const containerSizes = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
  full: '100%',
  screen: '100vw',
} as const;

export type DefaultContainerBreakpoints = typeof defaultContainerBreakpoints;
export type ContainerSizesMap = typeof containerSizes;
