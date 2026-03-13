import React from 'react';
import { UIAdaptationPolicy } from './adaptive-utils';

interface LayoutState {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  sidebarOpen: boolean;
  sidebarWidth: number;
}

// Context for sharing layout state
export const AdaptiveLayoutContext = React.createContext<{
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  sidebarOpen: boolean;
  sidebarWidth: number;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  openSidebar: () => void;
  expertiseLevel: string;
  adaptationPolicy: UIAdaptationPolicy;
}>({
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  sidebarOpen: true,
  sidebarWidth: 300,
  toggleSidebar: () => {},
  closeSidebar: () => {},
  openSidebar: () => {},
  expertiseLevel: 'intermediate',
  adaptationPolicy: {} as UIAdaptationPolicy
});


export type { LayoutState };