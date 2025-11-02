/**
 * Text Selection Provider Component
 * 
 * Ensures text selection works properly across the entire application.
 * Add this component to your app root or layout to enable text selection globally.
 */
import React, { useEffect } from 'react';
import { ensureTextSelectable } from '@/hooks/useTextSelection';
export interface TextSelectionProviderProps {
  children: React.ReactNode;
  enableGlobalSelection?: boolean;
  enableKeyboardShortcuts?: boolean;
  enableContextMenu?: boolean;
  debug?: boolean;
}
export function TextSelectionProvider({
  children,
  enableGlobalSelection = true,
  enableKeyboardShortcuts = true,
  enableContextMenu = true,
  debug = false,
}: TextSelectionProviderProps) {
  useEffect(() => {
    if (!enableGlobalSelection) return;
    // Ensure text selection is enabled globally
    const ensureGlobalSelection = () => {
      // Apply to document body
      if (document.body) {
        ensureTextSelectable(document.body);
      }
      // Apply to all existing elements
      const allElements = document.querySelectorAll('*');
      allElements.forEach((element) => {
        if (element instanceof HTMLElement) {
          // Skip elements that should not be selectable
          const skipTags = ['script', 'style', 'noscript'];
          if (!skipTags.includes(element.tagName.toLowerCase())) {
            ensureTextSelectable(element);
          }
        }
      });
    };
    // Run immediately
    ensureGlobalSelection();
    // Also run when DOM changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof HTMLElement) {
            ensureTextSelectable(node);
          }
        });
      });
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
    return () => {
      observer.disconnect();
    };
  }, [enableGlobalSelection]);
  useEffect(() => {
    if (!enableKeyboardShortcuts) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ctrl+A or Cmd+A - Select All
      if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
        // Let the browser handle this naturally
        if (debug) {
        }
      }
      // Ctrl+C or Cmd+C - Copy
      if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
        const selection = window.getSelection();
        if (selection && selection.toString()) {
          if (debug) {
            console.log('Copy triggered:', selection.toString());
          }
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [enableKeyboardShortcuts, debug]);
  useEffect(() => {
    if (!enableContextMenu) return;
    const handleContextMenu = (event: MouseEvent) => {
      // Allow context menu on text selections
      const selection = window.getSelection();
      if (selection && selection.toString()) {
        if (debug) {
          console.log('Context menu on selection:', selection.toString());
        }
        // Don't prevent default - allow context menu
        return;
      }
    };
    document.addEventListener('contextmenu', handleContextMenu);
    return () => {
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [enableContextMenu, debug]);
  useEffect(() => {
    if (!debug) return;
    const handleSelectionChange = () => {
      const selection = window.getSelection();
      if (selection && selection.toString()) {
        console.log('Selection changed:', selection.toString());
      }
    };
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
    };
  }, [debug]);
  return <>{children}</>;
}
// Higher-order component version
export function withTextSelection<P extends object>(
  Component: React.ComponentType<P>,
  options: Omit<TextSelectionProviderProps, 'children'> = {}
) {
  return function WrappedComponent(props: P) {
    return (
      <TextSelectionProvider {...options}>
        <Component {...props} />
      </TextSelectionProvider>
    );
  };
}
export default TextSelectionProvider;
