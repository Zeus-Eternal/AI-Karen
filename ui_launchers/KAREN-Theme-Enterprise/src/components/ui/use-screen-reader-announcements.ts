'use client';

import React from 'react';

import { useAriaAnnouncements } from './aria-live-announcements';

export interface ScreenReaderAnnouncementsApi {
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
  announceNavigation: (destination: string) => void;
  announceAction: (action: string) => void;
  announceError: (error: string) => void;
  announceSuccess: (message: string) => void;
  announceLoading: (message?: string) => void;
}

export function useScreenReaderAnnouncements(): ScreenReaderAnnouncementsApi {
  const { announce } = useAriaAnnouncements();

  const announceNavigation = React.useCallback((destination: string) => {
    announce(`Navigated to ${destination}`, 'polite');
  }, [announce]);

  const announceAction = React.useCallback((action: string) => {
    announce(`${action} completed`, 'polite');
  }, [announce]);

  const announceError = React.useCallback((error: string) => {
    announce(`Error: ${error}`, 'assertive');
  }, [announce]);

  const announceSuccess = React.useCallback((message: string) => {
    announce(`Success: ${message}`, 'polite');
  }, [announce]);

  const announceLoading = React.useCallback((message: string = 'Loading') => {
    announce(message, 'polite');
  }, [announce]);

  return {
    announce,
    announceNavigation,
    announceAction,
    announceError,
    announceSuccess,
    announceLoading,
  };
}
