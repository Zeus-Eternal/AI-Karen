/**
 * Text Selection and Interaction Hook
 * 
 * Provides utilities for text selection, copying, and interaction management.
 */
import { useCallback, useEffect, useState } from 'react';
export interface TextSelectionState {
  selectedText: string;
  selectionRange: Range | null;
  isSelecting: boolean;
}
export interface UseTextSelectionOptions {
  enableCopyShortcut?: boolean;
  onTextSelected?: (text: string, range: Range) => void;
  onTextCopied?: (text: string) => void;
}
export function useTextSelection(options: UseTextSelectionOptions = {}) {
  const {
    enableCopyShortcut = true,
    onTextSelected,
    onTextCopied,
  } = options;
  const [selectionState, setSelectionState] = useState<TextSelectionState>({
    selectedText: '',
    selectionRange: null,
    isSelecting: false,

  // Get current text selection
  const getCurrentSelection = useCallback((): TextSelectionState => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
      return {
        selectedText: '',
        selectionRange: null,
        isSelecting: false,
      };
    }
    const range = selection.getRangeAt(0);
    const selectedText = selection.toString();
    return {
      selectedText,
      selectionRange: range,
      isSelecting: selectedText.length > 0,
    };
  }, []);
  // Copy text to clipboard
  const copyToClipboard = useCallback(async (text: string): Promise<boolean> => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        onTextCopied?.(text);
        return true;
      } else {
        // Fallback for older browsers or non-secure contexts
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        const success = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (success) {
          onTextCopied?.(text);
        }
        return success;
      }
    } catch (error) {
      return false;
    }
  }, [onTextCopied]);
  // Copy current selection
  const copySelection = useCallback(async (): Promise<boolean> => {
    const currentSelection = getCurrentSelection();
    if (currentSelection.selectedText) {
      return await copyToClipboard(currentSelection.selectedText);
    }
    return false;
  }, [getCurrentSelection, copyToClipboard]);
  // Select all text in an element
  const selectAllInElement = useCallback((element: HTMLElement) => {
    const range = document.createRange();
    range.selectNodeContents(element);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
    const selectedText = selection?.toString() || '';
    if (selectedText && onTextSelected) {
      onTextSelected(selectedText, range);
    }
  }, [onTextSelected]);
  // Clear current selection
  const clearSelection = useCallback(() => {
    const selection = window.getSelection();
    selection?.removeAllRanges();
    setSelectionState({
      selectedText: '',
      selectionRange: null,
      isSelecting: false,

  }, []);
  // Handle selection change
  const handleSelectionChange = useCallback(() => {
    const newState = getCurrentSelection();
    setSelectionState(newState);
    if (newState.selectedText && newState.selectionRange && onTextSelected) {
      onTextSelected(newState.selectedText, newState.selectionRange);
    }
  }, [getCurrentSelection, onTextSelected]);
  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enableCopyShortcut) return;
    // Ctrl+C or Cmd+C
    if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
      const currentSelection = getCurrentSelection();
      if (currentSelection.selectedText) {
        // Let the browser handle the copy, but also trigger our callback
        setTimeout(() => {
          onTextCopied?.(currentSelection.selectedText);
        }, 0);
      }
    }
    // Ctrl+A or Cmd+A (select all)
    if ((event.ctrlKey || event.metaKey) && event.key === 'a') {
      // Let the browser handle select all, then update our state
      setTimeout(handleSelectionChange, 0);
    }
  }, [enableCopyShortcut, getCurrentSelection, onTextCopied, handleSelectionChange]);
  // Set up event listeners
  useEffect(() => {
    document.addEventListener('selectionchange', handleSelectionChange);
    if (enableCopyShortcut) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
      if (enableCopyShortcut) {
        document.removeEventListener('keydown', handleKeyDown);
      }
    };
  }, [handleSelectionChange, handleKeyDown, enableCopyShortcut]);
  // Utility to make an element's text easily selectable
  const makeSelectable = useCallback((element: HTMLElement) => {
    element.style.userSelect = 'auto';
    (element.style as any).webkitUserSelect = 'auto';
    (element.style as any).mozUserSelect = 'auto';
    (element.style as any).msUserSelect = 'auto';
    element.style.cursor = 'text';
  }, []);
  // Utility to make an element's text unselectable
  const makeUnselectable = useCallback((element: HTMLElement) => {
    element.style.userSelect = 'none';
    (element.style as any).webkitUserSelect = 'none';
    (element.style as any).mozUserSelect = 'none';
    (element.style as any).msUserSelect = 'none';
    element.style.cursor = 'default';
  }, []);
  return {
    // State
    selectionState,
    // Actions
    copyToClipboard,
    copySelection,
    selectAllInElement,
    clearSelection,
    getCurrentSelection,
    // Utilities
    makeSelectable,
    makeUnselectable,
    // Computed
    hasSelection: selectionState.isSelecting,
    selectedText: selectionState.selectedText,
  };
}
// Utility function to ensure text selection is enabled on an element
export function ensureTextSelectable(element: HTMLElement | null) {
  if (!element) return;
  element.style.userSelect = 'auto';
  (element.style as any).webkitUserSelect = 'auto';
  (element.style as any).mozUserSelect = 'auto';
  (element.style as any).msUserSelect = 'auto';
  // Also ensure child elements are selectable
  const children = element.querySelectorAll('*');
  children.forEach((child) => {
    if (child instanceof HTMLElement) {
      child.style.userSelect = 'auto';
      (child.style as any).webkitUserSelect = 'auto';
      (child.style as any).mozUserSelect = 'auto';
      (child.style as any).msUserSelect = 'auto';
    }

}
// Utility function to check if text selection is supported
export function isTextSelectionSupported(): boolean {
  return typeof window !== 'undefined' && 
         typeof window.getSelection === 'function' &&
         typeof document.createRange === 'function';
}
// Utility function to get selected text across the entire document
export function getDocumentSelection(): string {
  if (!isTextSelectionSupported()) return '';
  const selection = window.getSelection();
  return selection?.toString() || '';
}
// Utility function to highlight text selection with custom styling
export function highlightSelection(className: string = 'highlighted-selection') {
  if (!isTextSelectionSupported()) return;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return;
  const range = selection.getRangeAt(0);
  if (range.collapsed) return;
  try {
    const span = document.createElement('span');
    span.className = className;
    range.surroundContents(span);
  } catch (error) {
    // If surroundContents fails (e.g., range spans multiple elements),
    // we could implement a more complex highlighting solution
  }
}
// Debug function to test text selection
export function debugTextSelection() {
  console.log('Selection API supported:', isTextSelectionSupported());
  console.log('Current selection:', getDocumentSelection());
  // Test selection on body
  const selection = window.getSelection();
  // Check for conflicting CSS
  const testElement = document.createElement('div');
  testElement.textContent = 'Test selection';
  testElement.style.position = 'absolute';
  testElement.style.top = '-1000px';
  document.body.appendChild(testElement);
  const computedStyle = window.getComputedStyle(testElement);
  document.body.removeChild(testElement);
}
// Make debug function available in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).debugTextSelection = debugTextSelection;
}
