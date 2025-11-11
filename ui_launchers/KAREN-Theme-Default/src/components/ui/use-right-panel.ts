'use client';

import React from 'react';

export interface UseRightPanelState {
  isOpen: boolean;
  activeView?: string;
  openPanel: (viewId?: string) => void;
  closePanel: () => void;
  switchView: (viewId: string) => void;
  setActiveView: React.Dispatch<React.SetStateAction<string | undefined>>;
}

export function useRightPanel(initialView?: string): UseRightPanelState {
  const [isOpen, setIsOpen] = React.useState(false);
  const [activeView, setActiveView] = React.useState(initialView);

  const openPanel = React.useCallback((viewId?: string) => {
    setIsOpen(true);
    if (viewId) {
      setActiveView(viewId);
    }
  }, []);

  const closePanel = React.useCallback(() => {
    setIsOpen(false);
  }, []);

  const switchView = React.useCallback((viewId: string) => {
    setActiveView(viewId);
  }, []);

  return {
    isOpen,
    activeView,
    openPanel,
    closePanel,
    switchView,
    setActiveView,
  };
}
