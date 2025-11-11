/**
 * Keyboard Navigation Hook
 * Provides comprehensive keyboard navigation functionality for complex components
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface KeyboardNavigationOptions {
  /** Whether navigation is enabled */
  enabled?: boolean;
  /** Whether to loop navigation (go to first item after last) */
  loop?: boolean;
  /** Orientation of navigation */
  orientation?: 'horizontal' | 'vertical' | 'both';
  /** Custom key mappings */
  keyMap?: Partial<KeyMap>;
  /** Callback when active item changes */
  onActiveChange?: (index: number) => void;
  /** Callback when item is activated (Enter/Space) */
  onActivate?: (index: number) => void;
  /** Callback when escape is pressed */
  onEscape?: () => void;
  /** Whether to prevent default behavior for handled keys */
  preventDefault?: boolean;
}

export interface KeyMap {
  next: string[];
  previous: string[];
  first: string[];
  last: string[];
  activate: string[];
  escape: string[];
}

const DEFAULT_KEY_MAP: KeyMap = {
  next: ['ArrowDown', 'ArrowRight'],
  previous: ['ArrowUp', 'ArrowLeft'],
  first: ['Home'],
  last: ['End'],
  activate: ['Enter', ' '],
  escape: ['Escape'],
};

const HORIZONTAL_KEY_MAP: KeyMap = {
  next: ['ArrowRight'],
  previous: ['ArrowLeft'],
  first: ['Home'],
  last: ['End'],
  activate: ['Enter', ' '],
  escape: ['Escape'],
};

const VERTICAL_KEY_MAP: KeyMap = {
  next: ['ArrowDown'],
  previous: ['ArrowUp'],
  first: ['Home'],
  last: ['End'],
  activate: ['Enter', ' '],
  escape: ['Escape'],
};

/**
 * Hook for managing keyboard navigation in lists, grids, and other collections
 */
export const useKeyboardNavigation = (
  itemCount: number,
  options: KeyboardNavigationOptions = {}
) => {
  const {
    enabled = true,
    loop = true,
    orientation = 'vertical',
    keyMap: customKeyMap,
    onActiveChange,
    onActivate,
    onEscape,
    preventDefault = true,
  } = options;

  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLElement>(null);

  // Determine key map based on orientation
  const keyMap = useMemo(() => ({
    ...getKeyMapForOrientation(orientation),
    ...customKeyMap,
  }), [orientation, customKeyMap]);

  const moveToIndex = useCallback((index: number) => {
    if (index < 0 || index >= itemCount) return;
    
    setActiveIndex(index);
    onActiveChange?.(index);
    
    // Focus the item if it exists
    const container = containerRef.current;
    if (container) {
      const items = container.querySelectorAll('[role="option"], [role="menuitem"], [role="tab"], [role="gridcell"], [tabindex]');
      const item = items[index] as HTMLElement;
      if (item && typeof item.focus === 'function') {
        item.focus();
      }
    }
  }, [itemCount, onActiveChange]);

  const moveNext = useCallback(() => {
    const nextIndex = activeIndex + 1;
    if (nextIndex >= itemCount) {
      if (loop) {
        moveToIndex(0);
      }
    } else {
      moveToIndex(nextIndex);
    }
  }, [activeIndex, itemCount, loop, moveToIndex]);

  const movePrevious = useCallback(() => {
    const prevIndex = activeIndex - 1;
    if (prevIndex < 0) {
      if (loop) {
        moveToIndex(itemCount - 1);
      }
    } else {
      moveToIndex(prevIndex);
    }
  }, [activeIndex, itemCount, loop, moveToIndex]);

  const moveFirst = useCallback(() => {
    moveToIndex(0);
  }, [moveToIndex]);

  const moveLast = useCallback(() => {
    moveToIndex(itemCount - 1);
  }, [itemCount, moveToIndex]);

  const activate = useCallback(() => {
    if (activeIndex >= 0) {
      onActivate?.(activeIndex);
    }
  }, [activeIndex, onActivate]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled || itemCount === 0) return;

    const { key } = event;

    if (keyMap.next.includes(key)) {
      if (preventDefault) event.preventDefault();
      moveNext();
    } else if (keyMap.previous.includes(key)) {
      if (preventDefault) event.preventDefault();
      movePrevious();
    } else if (keyMap.first.includes(key)) {
      if (preventDefault) event.preventDefault();
      moveFirst();
    } else if (keyMap.last.includes(key)) {
      if (preventDefault) event.preventDefault();
      moveLast();
    } else if (keyMap.activate.includes(key)) {
      if (preventDefault) event.preventDefault();
      activate();
    } else if (keyMap.escape.includes(key)) {
      if (preventDefault) event.preventDefault();
      onEscape?.();
    }
  }, [
    enabled,
    itemCount,
    keyMap,
    preventDefault,
    moveNext,
    movePrevious,
    moveFirst,
    moveLast,
    activate,
    onEscape,
  ]);

  // Set up keyboard event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, enabled]);

  return {
    activeIndex,
    setActiveIndex: moveToIndex,
    moveNext,
    movePrevious,
    moveFirst,
    moveLast,
    activate,
    containerRef,
    containerProps: {
      ref: containerRef,
      onKeyDown: handleKeyDown,
    },
  };
};

/**
 * Hook for managing roving tabindex in a collection
 */
export const useRovingTabIndex = (
  itemCount: number,
  activeIndex: number = 0
) => {
  const getTabIndex = useCallback((index: number) => {
    return index === activeIndex ? 0 : -1;
  }, [activeIndex]);

  const getItemProps = useCallback((index: number) => ({
    tabIndex: getTabIndex(index),
  }), [getTabIndex]);

  return {
    getTabIndex,
    getItemProps,
  };
};

/**
 * Hook for managing grid navigation (2D navigation)
 */
export interface GridNavigationOptions extends Omit<KeyboardNavigationOptions, 'orientation'> {
  /** Number of columns in the grid */
  columns: number;
  /** Number of rows in the grid */
  rows: number;
}

export const useGridNavigation = (options: GridNavigationOptions) => {
  const { columns, rows, ...navigationOptions } = options;

  const [activeRow, setActiveRow] = useState(0);
  const [activeCol, setActiveCol] = useState(0);

  const activeIndex = activeRow * columns + activeCol;

  const moveToCell = useCallback((row: number, col: number) => {
    if (row < 0 || row >= rows || col < 0 || col >= columns) return;
    
    setActiveRow(row);
    setActiveCol(col);
    navigationOptions.onActiveChange?.(row * columns + col);
  }, [rows, columns, navigationOptions]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!navigationOptions.enabled) return;

    const { key } = event;

    switch (key) {
      case 'ArrowUp':
        event.preventDefault();
        moveToCell(activeRow - 1, activeCol);
        break;
      case 'ArrowDown':
        event.preventDefault();
        moveToCell(activeRow + 1, activeCol);
        break;
      case 'ArrowLeft':
        event.preventDefault();
        moveToCell(activeRow, activeCol - 1);
        break;
      case 'ArrowRight':
        event.preventDefault();
        moveToCell(activeRow, activeCol + 1);
        break;
      case 'Home':
        event.preventDefault();
        if (event.ctrlKey) {
          moveToCell(0, 0); // Go to first cell
        } else {
          moveToCell(activeRow, 0); // Go to first cell in row
        }
        break;
      case 'End':
        event.preventDefault();
        if (event.ctrlKey) {
          moveToCell(rows - 1, columns - 1); // Go to last cell
        } else {
          moveToCell(activeRow, columns - 1); // Go to last cell in row
        }
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        navigationOptions.onActivate?.(activeIndex);
        break;
      case 'Escape':
        event.preventDefault();
        navigationOptions.onEscape?.();
        break;
    }
  }, [
    navigationOptions,
    activeRow,
    activeCol,
    activeIndex,
    rows,
    columns,
    moveToCell,
  ]);

  return {
    activeRow,
    activeCol,
    activeIndex,
    moveToCell,
    containerProps: {
      onKeyDown: handleKeyDown,
    },
  };
};

// Helper function to get key map based on orientation
function getKeyMapForOrientation(orientation: 'horizontal' | 'vertical' | 'both'): KeyMap {
  switch (orientation) {
    case 'horizontal':
      return HORIZONTAL_KEY_MAP;
    case 'vertical':
      return VERTICAL_KEY_MAP;
    case 'both':
    default:
      return DEFAULT_KEY_MAP;
  }
}