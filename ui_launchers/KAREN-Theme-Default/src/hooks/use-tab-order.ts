'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export interface TabOrderItem {
  id: string;
  element: HTMLElement | null;
  tabIndex: number;
  focusable: boolean;
  disabled?: boolean;
  onFocus?: () => void;
  onBlur?: () => void;
}

export interface TabOrderOptions {
  enabled?: boolean;
  rovingTabIndex?: boolean;
  initialFocus?: string;
  loop?: boolean;
  onFocusChange?: (itemId: string | null) => void;
}

export const useTabOrder = (options: TabOrderOptions = {}) => {
  const {
    enabled = true,
    rovingTabIndex = false,
    initialFocus,
    loop = true,
    onFocusChange,
  } = options;

  const [items, setItems] = useState<Map<string, TabOrderItem>>(new Map());
  const [focusedItemId, setFocusedItemId] = useState<string | null>(initialFocus || null);
  const containerRef = useRef<HTMLElement>(null);

  const registerItem = useCallback((item: Omit<TabOrderItem, 'tabIndex'>) => {
    setItems(prev => {
      const newItems = new Map(prev);
      const tabIndex = rovingTabIndex 
        ? (item.id === focusedItemId ? 0 : -1)
        : item.focusable ? 0 : -1;
      
      newItems.set(item.id, { ...item, tabIndex });
      return newItems;
    });
  }, [rovingTabIndex, focusedItemId]);

  const unregisterItem = useCallback((id: string) => {
    setItems(prev => {
      const newItems = new Map(prev);
      newItems.delete(id);
      return newItems;
    });
  }, []);

  const updateItem = useCallback((id: string, updates: Partial<TabOrderItem>) => {
    setItems(prev => {
      const newItems = new Map(prev);
      const existing = newItems.get(id);
      if (existing) {
        newItems.set(id, { ...existing, ...updates });
      }
      return newItems;
    });
  }, []);

  const getFocusableItems = useCallback(() => {
    return Array.from(items.values())
      .filter(item => item.focusable && !item.disabled && item.element)
      .sort((a, b) => {
        if (a.element && b.element) {
          const position = a.element.compareDocumentPosition(b.element);
          if (position & Node.DOCUMENT_POSITION_FOLLOWING) return -1;
          if (position & Node.DOCUMENT_POSITION_PRECEDING) return 1;
        }
        return 0;
      });
  }, [items]);

  const focusItem = useCallback((id: string) => {
    const item = items.get(id);
    if (!item || !item.focusable || item.disabled || !item.element) return false;

    item.element.focus();
    setFocusedItemId(id);
    onFocusChange?.(id);
    item.onFocus?.();

    if (rovingTabIndex) {
      setItems(prev => {
        const newItems = new Map(prev);
        newItems.forEach((item, itemId) => {
          const tabIndex = itemId === id ? 0 : -1;
          newItems.set(itemId, { ...item, tabIndex });
        });
        return newItems;
      });
    }

    return true;
  }, [items, rovingTabIndex, onFocusChange]);

  const focusNext = useCallback(() => {
    const focusableItems = getFocusableItems();
    if (focusableItems.length === 0) return false;

    const currentIndex = focusedItemId 
      ? focusableItems.findIndex(item => item.id === focusedItemId)
      : -1;

    let nextIndex = currentIndex + 1;
    if (nextIndex >= focusableItems.length) {
      nextIndex = loop ? 0 : focusableItems.length - 1;
    }

    return focusItem(focusableItems[nextIndex].id);
  }, [getFocusableItems, focusedItemId, loop, focusItem]);

  const focusPrevious = useCallback(() => {
    const focusableItems = getFocusableItems();
    if (focusableItems.length === 0) return false;

    const currentIndex = focusedItemId 
      ? focusableItems.findIndex(item => item.id === focusedItemId)
      : -1;

    let prevIndex = currentIndex - 1;
    if (prevIndex < 0) {
      prevIndex = loop ? focusableItems.length - 1 : 0;
    }

    return focusItem(focusableItems[prevIndex].id);
  }, [getFocusableItems, focusedItemId, loop, focusItem]);

  const focusFirst = useCallback(() => {
    const focusableItems = getFocusableItems();
    if (focusableItems.length === 0) return false;
    return focusItem(focusableItems[0].id);
  }, [getFocusableItems, focusItem]);

  const focusLast = useCallback(() => {
    const focusableItems = getFocusableItems();
    if (focusableItems.length === 0) return false;
    return focusItem(focusableItems[focusableItems.length - 1].id);
  }, [getFocusableItems, focusItem]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return;

    switch (event.key) {
      case 'Tab':
        if (rovingTabIndex) {
          event.preventDefault();
          if (event.shiftKey) {
            focusPrevious();
          } else {
            focusNext();
          }
        }
        break;
      case 'ArrowDown':
      case 'ArrowRight':
        if (rovingTabIndex) {
          event.preventDefault();
          focusNext();
        }
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        if (rovingTabIndex) {
          event.preventDefault();
          focusPrevious();
        }
        break;
      case 'Home':
        if (rovingTabIndex) {
          event.preventDefault();
          focusFirst();
        }
        break;
      case 'End':
        if (rovingTabIndex) {
          event.preventDefault();
          focusLast();
        }
        break;
    }
  }, [enabled, rovingTabIndex, focusNext, focusPrevious, focusFirst, focusLast]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    container.addEventListener('keydown', handleKeyDown);
    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown, enabled]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    const handleFocus = (event: FocusEvent) => {
      const target = event.target as HTMLElement;
      
      for (const [id, item] of items) {
        if (item.element === target || item.element?.contains(target)) {
          setFocusedItemId(id);
          onFocusChange?.(id);
          item.onFocus?.();
          break;
        }
      }
    };

    const handleBlur = (event: FocusEvent) => {
      const target = event.target as HTMLElement;
      
      for (const [id, item] of items) {
        if (item.element === target || item.element?.contains(target)) {
          item.onBlur?.();
          break;
        }
      }

      const relatedTarget = event.relatedTarget as HTMLElement;
      if (!relatedTarget || !container.contains(relatedTarget)) {
        setFocusedItemId(null);
        onFocusChange?.(null);
      }
    };

    container.addEventListener('focus', handleFocus, true);
    container.addEventListener('blur', handleBlur, true);

    return () => {
      container.removeEventListener('focus', handleFocus, true);
      container.removeEventListener('blur', handleBlur, true);
    };
  }, [items, enabled, onFocusChange]);

  useEffect(() => {
    if (initialFocus && items.has(initialFocus) && !focusedItemId) {
      focusItem(initialFocus);
    }
  }, [initialFocus, items, focusedItemId, focusItem]);

  return {
    containerRef,
    focusedItemId,
    registerItem,
    unregisterItem,
    updateItem,
    focusItem,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    getFocusableItems,
    containerProps: {
      ref: containerRef,
      onKeyDown: handleKeyDown,
    },
  };
};

export const useTabOrderItem = (
  id: string,
  tabOrder: ReturnType<typeof useTabOrder>,
  options: {
    focusable?: boolean;
    disabled?: boolean;
    onFocus?: () => void;
    onBlur?: () => void;
  } = {}
) => {
  const { focusable = true, disabled = false, onFocus, onBlur } = options;
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (elementRef.current) {
      tabOrder.registerItem({
        id,
        element: elementRef.current,
        focusable: focusable && !disabled,
        disabled,
        onFocus,
        onBlur,
      });
    }

    return () => {
      tabOrder.unregisterItem(id);
    };
  }, [id, focusable, disabled, onFocus, onBlur, tabOrder]);

  useEffect(() => {
    if (elementRef.current) {
      tabOrder.updateItem(id, { element: elementRef.current });
    }
  }, [id, tabOrder]);

  const isFocused = tabOrder.focusedItemId === id;
  const tabIndex = focusable && !disabled ? (isFocused ? 0 : -1) : -1;

  return {
    elementRef,
    isFocused,
    tabIndex,
    focus: () => tabOrder.focusItem(id),
    itemProps: {
      ref: elementRef,
      tabIndex,
      'data-tab-order-id': id,
    },
  };
};

export default useTabOrder;
