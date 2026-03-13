"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type ActiveView = 
  | 'chat' 
  | 'settings' 
  | 'commsCenter' 
  | 'pluginDatabaseConnector' 
  | 'pluginFacebook' 
  | 'pluginGmail' 
  | 'pluginDateTime' 
  | 'pluginWeather' 
  | 'pluginOverview' 
  | 'memory' 
  | 'files' 
  | 'admin' 
  | 'performance';

export interface NavigationItem {
  id: ActiveView;
  label: string;
  icon: ReactNode;
  description: string;
  category: 'main' | 'plugin';
  badge?: string | number;
  disabled?: boolean;
}

export interface NavigationContextType {
  activeView: ActiveView;
  setActiveView: (view: ActiveView) => void;
  navigationHistory: ActiveView[];
  navigateBack: () => void;
  canNavigateBack: boolean;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filteredNavigationItems: NavigationItem[];
  isSearchMode: boolean;
  setIsSearchMode: (enabled: boolean) => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
};

interface NavigationProviderProps {
  children: ReactNode;
  defaultView?: ActiveView;
}

const navigationItems: NavigationItem[] = [
  // Main navigation items
  {
    id: 'chat',
    label: 'Chat',
    icon: '💬',
    description: 'Chat with Karen AI',
    category: 'main'
  },
  {
    id: 'memory',
    label: 'Memory',
    icon: '🧠',
    description: 'View and manage memory',
    category: 'main'
  },
  {
    id: 'files',
    label: 'Files',
    icon: '📁',
    description: 'View and manage files',
    category: 'main'
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    description: 'Configure application settings',
    category: 'main'
  },
  {
    id: 'commsCenter',
    label: 'Comms Center',
    icon: '🔔',
    description: 'View notifications and communications',
    category: 'main'
  },
  {
    id: 'performance',
    label: 'Performance',
    icon: '📊',
    description: 'View system performance metrics',
    category: 'main'
  },
  {
    id: 'admin',
    label: 'Admin',
    icon: '🛡️',
    description: 'Access administrative functions',
    category: 'main'
  },
  // Plugin navigation items
  {
    id: 'pluginOverview',
    label: 'Plugin Overview',
    icon: '🔌',
    description: 'View all available plugins',
    category: 'plugin'
  },
  {
    id: 'pluginDatabaseConnector',
    label: 'Database Connector',
    icon: '🗄️',
    description: 'Connect to external databases',
    category: 'plugin'
  },
  {
    id: 'pluginFacebook',
    label: 'Facebook Integration',
    icon: '📘',
    description: 'Connect to Facebook services',
    category: 'plugin'
  },
  {
    id: 'pluginGmail',
    label: 'Gmail Integration',
    icon: '📧',
    description: 'Connect to Gmail services',
    category: 'plugin'
  },
  {
    id: 'pluginDateTime',
    label: 'Date/Time Service',
    icon: '📅',
    description: 'Access date and time services',
    category: 'plugin'
  },
  {
    id: 'pluginWeather',
    label: 'Weather Service',
    icon: '🌤️',
    description: 'Access weather information',
    category: 'plugin'
  }
];

export const NavigationProvider: React.FC<NavigationProviderProps> = ({ 
  children, 
  defaultView = 'chat' 
}) => {
  const [activeView, setActiveViewState] = useState<ActiveView>(defaultView);
  const [navigationHistory, setNavigationHistory] = useState<ActiveView[]>([defaultView]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchMode, setIsSearchMode] = useState(false);

  const setActiveView = useCallback((view: ActiveView) => {
    setActiveViewState(view);
    setNavigationHistory(prev => [...prev, view]);
    setIsSearchMode(false);
    setSearchQuery('');
  }, []);

  const navigateBack = useCallback(() => {
    if (navigationHistory.length > 1) {
      const previousView = navigationHistory[navigationHistory.length - 2];
      setActiveViewState(previousView);
      setNavigationHistory(prev => prev.slice(0, -1));
    }
  }, [navigationHistory]);

  const filteredNavigationItems = navigationItems.filter(item =>
    item.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const canNavigateBack = navigationHistory.length > 1;

  const value: NavigationContextType = {
    activeView,
    setActiveView,
    navigationHistory,
    navigateBack,
    canNavigateBack,
    searchQuery,
    setSearchQuery,
    filteredNavigationItems,
    isSearchMode,
    setIsSearchMode,
  };

  return (
    <NavigationContext.Provider value={value}>
      {children}
    </NavigationContext.Provider>
  );
};

export { navigationItems };