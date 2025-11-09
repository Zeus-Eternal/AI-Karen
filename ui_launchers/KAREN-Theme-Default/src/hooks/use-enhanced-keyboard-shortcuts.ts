// ui_launchers/KAREN-Theme-Default/src/hooks/use-enhanced-keyboard-shortcuts.ts
"use client";

import { useCallback, useEffect, useRef, useState } from 'react';
import {  useKeyboardShortcuts, type KeyboardShortcutConfig, type KeyboardShortcutHandler } from './use-keyboard-shortcuts';

export interface EnhancedKeyboardShortcutConfig extends KeyboardShortcutConfig {
  /** Whether this shortcut should be announced to screen readers */
  announce?: boolean;
  /** Custom announcement text */
  announcementText?: string;
  /** Whether this shortcut is context-sensitive */
  contextSensitive?: boolean;
  /** Function to check if shortcut should be active in current context */
  isActive?: () => boolean;
  /** Priority level for conflicting shortcuts */
  priority?: number;
}

export interface KeyboardShortcutContext {
  /** Current context name */
  context: string;
  /** Whether shortcuts are globally enabled */
  enabled: boolean;
  /** Function to announce shortcut activation */
  announce: (message: string) => void;
}

/**
 * Enhanced keyboard shortcuts hook with accessibility features
 */
export const useEnhancedKeyboardShortcuts = (
  shortcuts: EnhancedKeyboardShortcutConfig[],
  context: KeyboardShortcutContext
) => {
  const [activeShortcuts, setActiveShortcuts] = useState<KeyboardShortcutConfig[]>([]);

  // Filter and sort shortcuts based on context and priority
  useEffect(() => {
    const filtered = shortcuts
      .filter(shortcut => {
        if (!context.enabled) return false;
        if (shortcut.contextSensitive && shortcut.isActive) {
          return shortcut.isActive();
        }
        return true;
      })
      .sort((a, b) => (b.priority || 0) - (a.priority || 0))
      .map(shortcut => ({
        ...shortcut,
        handler: (event: KeyboardEvent) => {
          // Announce shortcut activation if needed
          if (shortcut.announce && context.announce) {
            const announcement = shortcut.announcementText || 
              `${shortcut.description || 'Shortcut'} activated`;
            context.announce(announcement);
          }
          
          // Call original handler
          shortcut.handler(event);
        }
      }));

    setActiveShortcuts(filtered);
  }, [shortcuts, context]);

  useKeyboardShortcuts(activeShortcuts, context.enabled);

  return {
    activeShortcuts: activeShortcuts.length,
    context: context.context,
  };
};

/**
 * Hook for modal/dialog keyboard shortcuts
 */
export const useModalKeyboardShortcuts = (
  isOpen: boolean,
  onClose: () => void,
  onConfirm?: () => void,
  announce?: (message: string) => void
) => {
  const shortcuts: EnhancedKeyboardShortcutConfig[] = [
    {
      key: 'Escape',
      handler: () => onClose(),
      description: 'Close modal',
      category: 'Modal',
      announce: true,
      announcementText: 'Modal closed',
      priority: 100,
    },
  ];

  if (onConfirm) {
    shortcuts.push({
      key: 'Enter',
      ctrlKey: true,
      handler: () => onConfirm(),
      description: 'Confirm action',
      category: 'Modal',
      announce: true,
      announcementText: 'Action confirmed',
      priority: 90,
    });
  }

  useEnhancedKeyboardShortcuts(shortcuts, {
    context: 'modal',
    enabled: isOpen,
    announce: announce || (() => {}),
  });
};

/**
 * Hook for form keyboard shortcuts
 */
export const useFormKeyboardShortcuts = (
  onSubmit?: () => void,
  onReset?: () => void,
  onCancel?: () => void,
  announce?: (message: string) => void
) => {
  const shortcuts: EnhancedKeyboardShortcutConfig[] = [];

  if (onSubmit) {
    shortcuts.push({
      key: 'Enter',
      ctrlKey: true,
      handler: () => onSubmit(),
      description: 'Submit form',
      category: 'Form',
      announce: true,
      announcementText: 'Form submitted',
    });
  }

  if (onReset) {
    shortcuts.push({
      key: 'r',
      ctrlKey: true,
      shiftKey: true,
      handler: () => onReset(),
      description: 'Reset form',
      category: 'Form',
      announce: true,
      announcementText: 'Form reset',
    });
  }

  if (onCancel) {
    shortcuts.push({
      key: 'Escape',
      handler: () => onCancel(),
      description: 'Cancel form',
      category: 'Form',
      announce: true,
      announcementText: 'Form cancelled',
    });
  }

  useEnhancedKeyboardShortcuts(shortcuts, {
    context: 'form',
    enabled: true,
    announce: announce || (() => {}),
  });
};

/**
 * Hook for table/grid keyboard shortcuts
 */
export const useTableKeyboardShortcuts = (
  onSelectAll?: () => void,
  onClearSelection?: () => void,
  onDelete?: () => void,
  onEdit?: () => void,
  announce?: (message: string) => void
) => {
  const shortcuts: EnhancedKeyboardShortcutConfig[] = [];

  if (onSelectAll) {
    shortcuts.push({
      key: 'a',
      ctrlKey: true,
      handler: () => onSelectAll(),
      description: 'Select all items',
      category: 'Table',
      announce: true,
      announcementText: 'All items selected',
    });
  }

  if (onClearSelection) {
    shortcuts.push({
      key: 'Escape',
      handler: () => onClearSelection(),
      description: 'Clear selection',
      category: 'Table',
      announce: true,
      announcementText: 'Selection cleared',
    });
  }

  if (onDelete) {
    shortcuts.push({
      key: 'Delete',
      handler: () => onDelete(),
      description: 'Delete selected items',
      category: 'Table',
      announce: true,
      announcementText: 'Items deleted',
    });
  }

  if (onEdit) {
    shortcuts.push({
      key: 'Enter',
      handler: () => onEdit(),
      description: 'Edit selected item',
      category: 'Table',
      announce: true,
      announcementText: 'Edit mode activated',
    });
  }

  useEnhancedKeyboardShortcuts(shortcuts, {
    context: 'table',
    enabled: true,
    announce: announce || (() => {}),
  });
};

/**
 * Hook for search keyboard shortcuts
 */
export const useSearchKeyboardShortcuts = (
  onFocus?: () => void,
  onClear?: () => void,
  onNext?: () => void,
  onPrevious?: () => void,
  announce?: (message: string) => void
) => {
  const shortcuts: EnhancedKeyboardShortcutConfig[] = [];

  if (onFocus) {
    shortcuts.push({
      key: 'f',
      ctrlKey: true,
      handler: () => onFocus(),
      description: 'Focus search',
      category: 'Search',
      announce: true,
      announcementText: 'Search focused',
    });

    shortcuts.push({
      key: '/',
      handler: () => onFocus(),
      description: 'Focus search',
      category: 'Search',
      announce: true,
      announcementText: 'Search focused',
    });
  }

  if (onClear) {
    shortcuts.push({
      key: 'Escape',
      handler: () => onClear(),
      description: 'Clear search',
      category: 'Search',
      announce: true,
      announcementText: 'Search cleared',
    });
  }

  if (onNext) {
    shortcuts.push({
      key: 'g',
      ctrlKey: true,
      handler: () => onNext(),
      description: 'Next result',
      category: 'Search',
      announce: true,
      announcementText: 'Next search result',
    });

    shortcuts.push({
      key: 'F3',
      handler: () => onNext(),
      description: 'Next result',
      category: 'Search',
      announce: true,
      announcementText: 'Next search result',
    });
  }

  if (onPrevious) {
    shortcuts.push({
      key: 'g',
      ctrlKey: true,
      shiftKey: true,
      handler: () => onPrevious(),
      description: 'Previous result',
      category: 'Search',
      announce: true,
      announcementText: 'Previous search result',
    });

    shortcuts.push({
      key: 'F3',
      shiftKey: true,
      handler: () => onPrevious(),
      description: 'Previous result',
      category: 'Search',
      announce: true,
      announcementText: 'Previous search result',
    });
  }

  useEnhancedKeyboardShortcuts(shortcuts, {
    context: 'search',
    enabled: true,
    announce: announce || (() => {}),
  });
};

/**
 * Hook for managing keyboard shortcut help overlay
 */
export const useKeyboardShortcutHelp = () => {
  const [isHelpVisible, setIsHelpVisible] = useState(false);

  const toggleHelp = useCallback(() => {
    setIsHelpVisible(prev => !prev);
  }, []);

  const hideHelp = useCallback(() => {
    setIsHelpVisible(false);
  }, []);

  // Global shortcut to show help
  useEnhancedKeyboardShortcuts([
    {
      key: '?',
      shiftKey: true,
      handler: toggleHelp,
      description: 'Show keyboard shortcuts help',
      category: 'Help',
      announce: true,
      announcementText: isHelpVisible ? 'Help hidden' : 'Help shown',
    },
    {
      key: 'F1',
      handler: toggleHelp,
      description: 'Show keyboard shortcuts help',
      category: 'Help',
      announce: true,
      announcementText: isHelpVisible ? 'Help hidden' : 'Help shown',
    },
  ], {
    context: 'global',
    enabled: true,
    announce: () => {},
  });

  return {
    isHelpVisible,
    toggleHelp,
    hideHelp,
  };
};

/**
 * Hook for managing escape key handling in nested contexts
 */
export const useEscapeKeyHandler = (
  handler: () => void,
  priority: number = 0,
  enabled: boolean = true
) => {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    if (!enabled) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        handlerRef.current();
      }
    };

    // Add event listener with capture to handle in priority order
    document.addEventListener('keydown', handleEscape, true);

    return () => {
      document.removeEventListener('keydown', handleEscape, true);
    };
  }, [enabled, priority]);
};

export default useEnhancedKeyboardShortcuts;
