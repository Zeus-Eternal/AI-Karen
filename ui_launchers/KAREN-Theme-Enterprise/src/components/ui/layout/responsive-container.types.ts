import type * as React from 'react';

export interface ContainerBreakpoints {
  xs?: string;
  sm?: string;
  md?: string;
  lg?: string;
  xl?: string;
  '2xl'?: string;
}

export interface ResponsiveValue<T> {
  base?: T;
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  '2xl'?: T;
}

export type ContainerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full' | 'screen';

export interface ResponsiveContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: ContainerSize | ResponsiveValue<ContainerSize>;
  containerQueries?: boolean;
  containerName?: string;
  breakpoints?: ContainerBreakpoints;
  padding?: string | ResponsiveValue<string>;
  margin?: string | ResponsiveValue<string>;
  center?: boolean;
  fluid?: boolean;
  responsive?: boolean;
  minHeight?: string;
  maxHeight?: string;
  background?: string;
  borderRadius?: string;
  shadow?: string;
  children: React.ReactNode;
}
