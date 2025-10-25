"use client"

import { useEffect, useCallback, useRef } from "react"

// Types for keyboard shortcuts
export interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  metaKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  preventDefault?: boolean
  stopPropagation?: boolean
  description?: string
  category?: string
}

export interface KeyboardShortcutHandler {
  (event: KeyboardEvent): void
}

export interface KeyboardShortcutConfig extends KeyboardShortcut {
  handler: KeyboardShortcutHandler
}

/**
 * Hook for managing keyboard shortcuts
 * 
 * @param shortcuts - Array of keyboard shortcut configurations
 * @param enabled - Whether shortcuts are enabled (default: true)
 * @param target - Target element for event listeners (default: document)
 */
export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcutConfig[],
  enabled: boolean = true,
  target: EventTarget | null = null
) {
  const shortcutsRef = useRef(shortcuts)
  shortcutsRef.current = shortcuts

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!enabled) return

    for (const shortcut of shortcutsRef.current) {
      if (matchesShortcut(event, shortcut)) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault()
        }
        if (shortcut.stopPropagation) {
          event.stopPropagation()
        }
        shortcut.handler(event)
        break // Only execute the first matching shortcut
      }
    }
  }, [enabled])

  useEffect(() => {
    const eventTarget = target || (typeof document !== "undefined" ? document : null)
    if (!eventTarget || !enabled) return

    eventTarget.addEventListener("keydown", handleKeyDown as EventListener)
    
    return () => {
      eventTarget.removeEventListener("keydown", handleKeyDown as EventListener)
    }
  }, [handleKeyDown, enabled, target])
}

/**
 * Hook for a single keyboard shortcut
 * 
 * @param shortcut - Keyboard shortcut configuration
 * @param handler - Handler function
 * @param enabled - Whether shortcut is enabled (default: true)
 * @param target - Target element for event listeners (default: document)
 */
export function useKeyboardShortcut(
  shortcut: KeyboardShortcut,
  handler: KeyboardShortcutHandler,
  enabled: boolean = true,
  target: EventTarget | null = null
) {
  const shortcuts = [{ ...shortcut, handler }]
  useKeyboardShortcuts(shortcuts, enabled, target)
}

/**
 * Hook for common application shortcuts
 * 
 * @param handlers - Object with handler functions for common shortcuts
 * @param enabled - Whether shortcuts are enabled (default: true)
 */
export function useCommonShortcuts(
  handlers: {
    save?: KeyboardShortcutHandler
    copy?: KeyboardShortcutHandler
    paste?: KeyboardShortcutHandler
    cut?: KeyboardShortcutHandler
    undo?: KeyboardShortcutHandler
    redo?: KeyboardShortcutHandler
    selectAll?: KeyboardShortcutHandler
    find?: KeyboardShortcutHandler
    newItem?: KeyboardShortcutHandler
    delete?: KeyboardShortcutHandler
    escape?: KeyboardShortcutHandler
    enter?: KeyboardShortcutHandler
  },
  enabled: boolean = true
) {
  const shortcuts: KeyboardShortcutConfig[] = []

  if (handlers.save) {
    shortcuts.push({
      key: "s",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.save,
      description: "Save",
      category: "File",
    })
  }

  if (handlers.copy) {
    shortcuts.push({
      key: "c",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.copy,
      description: "Copy",
      category: "Edit",
    })
  }

  if (handlers.paste) {
    shortcuts.push({
      key: "v",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.paste,
      description: "Paste",
      category: "Edit",
    })
  }

  if (handlers.cut) {
    shortcuts.push({
      key: "x",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.cut,
      description: "Cut",
      category: "Edit",
    })
  }

  if (handlers.undo) {
    shortcuts.push({
      key: "z",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.undo,
      description: "Undo",
      category: "Edit",
    })
  }

  if (handlers.redo) {
    shortcuts.push({
      key: "z",
      ctrlKey: true,
      metaKey: true,
      shiftKey: true,
      handler: handlers.redo,
      description: "Redo",
      category: "Edit",
    })
  }

  if (handlers.selectAll) {
    shortcuts.push({
      key: "a",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.selectAll,
      description: "Select All",
      category: "Edit",
    })
  }

  if (handlers.find) {
    shortcuts.push({
      key: "f",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.find,
      description: "Find",
      category: "Search",
    })
  }

  if (handlers.newItem) {
    shortcuts.push({
      key: "n",
      ctrlKey: true,
      metaKey: true,
      handler: handlers.newItem,
      description: "New",
      category: "File",
    })
  }

  if (handlers.delete) {
    shortcuts.push({
      key: "Delete",
      handler: handlers.delete,
      description: "Delete",
      category: "Edit",
    })
  }

  if (handlers.escape) {
    shortcuts.push({
      key: "Escape",
      handler: handlers.escape,
      description: "Cancel/Close",
      category: "Navigation",
    })
  }

  if (handlers.enter) {
    shortcuts.push({
      key: "Enter",
      handler: handlers.enter,
      description: "Confirm/Submit",
      category: "Navigation",
    })
  }

  useKeyboardShortcuts(shortcuts, enabled)
}

/**
 * Hook for navigation shortcuts (arrow keys, tab, etc.)
 * 
 * @param handlers - Object with handler functions for navigation
 * @param enabled - Whether shortcuts are enabled (default: true)
 */
export function useNavigationShortcuts(
  handlers: {
    arrowUp?: KeyboardShortcutHandler
    arrowDown?: KeyboardShortcutHandler
    arrowLeft?: KeyboardShortcutHandler
    arrowRight?: KeyboardShortcutHandler
    home?: KeyboardShortcutHandler
    end?: KeyboardShortcutHandler
    pageUp?: KeyboardShortcutHandler
    pageDown?: KeyboardShortcutHandler
    tab?: KeyboardShortcutHandler
    shiftTab?: KeyboardShortcutHandler
  },
  enabled: boolean = true
) {
  const shortcuts: KeyboardShortcutConfig[] = []

  if (handlers.arrowUp) {
    shortcuts.push({
      key: "ArrowUp",
      handler: handlers.arrowUp,
      description: "Move Up",
      category: "Navigation",
    })
  }

  if (handlers.arrowDown) {
    shortcuts.push({
      key: "ArrowDown",
      handler: handlers.arrowDown,
      description: "Move Down",
      category: "Navigation",
    })
  }

  if (handlers.arrowLeft) {
    shortcuts.push({
      key: "ArrowLeft",
      handler: handlers.arrowLeft,
      description: "Move Left",
      category: "Navigation",
    })
  }

  if (handlers.arrowRight) {
    shortcuts.push({
      key: "ArrowRight",
      handler: handlers.arrowRight,
      description: "Move Right",
      category: "Navigation",
    })
  }

  if (handlers.home) {
    shortcuts.push({
      key: "Home",
      handler: handlers.home,
      description: "Go to Start",
      category: "Navigation",
    })
  }

  if (handlers.end) {
    shortcuts.push({
      key: "End",
      handler: handlers.end,
      description: "Go to End",
      category: "Navigation",
    })
  }

  if (handlers.pageUp) {
    shortcuts.push({
      key: "PageUp",
      handler: handlers.pageUp,
      description: "Page Up",
      category: "Navigation",
    })
  }

  if (handlers.pageDown) {
    shortcuts.push({
      key: "PageDown",
      handler: handlers.pageDown,
      description: "Page Down",
      category: "Navigation",
    })
  }

  if (handlers.tab) {
    shortcuts.push({
      key: "Tab",
      handler: handlers.tab,
      description: "Next Item",
      category: "Navigation",
    })
  }

  if (handlers.shiftTab) {
    shortcuts.push({
      key: "Tab",
      shiftKey: true,
      handler: handlers.shiftTab,
      description: "Previous Item",
      category: "Navigation",
    })
  }

  useKeyboardShortcuts(shortcuts, enabled)
}

/**
 * Hook to get formatted shortcut display string
 * 
 * @param shortcut - Keyboard shortcut configuration
 * @returns Formatted string for display (e.g., "Ctrl+S", "⌘+S")
 */
export function useShortcutDisplay(shortcut: KeyboardShortcut): string {
  const isMac = typeof navigator !== "undefined" && navigator.platform.toUpperCase().indexOf("MAC") >= 0

  const parts: string[] = []

  if (shortcut.ctrlKey || shortcut.metaKey) {
    parts.push(isMac ? "⌘" : "Ctrl")
  }

  if (shortcut.altKey) {
    parts.push(isMac ? "⌥" : "Alt")
  }

  if (shortcut.shiftKey) {
    parts.push(isMac ? "⇧" : "Shift")
  }

  // Format key name
  let keyName = shortcut.key
  if (keyName.length === 1) {
    keyName = keyName.toUpperCase()
  } else {
    // Handle special keys
    const keyMap: Record<string, string> = {
      ArrowUp: "↑",
      ArrowDown: "↓",
      ArrowLeft: "←",
      ArrowRight: "→",
      Escape: "Esc",
      Delete: "Del",
      Backspace: "⌫",
      Enter: "↵",
      Tab: "⇥",
      Space: "Space",
    }
    keyName = keyMap[keyName] || keyName
  }

  parts.push(keyName)

  return parts.join(isMac ? "" : "+")
}

// Helper function to check if event matches shortcut
function matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
  // Check key
  if (event.key.toLowerCase() !== shortcut.key.toLowerCase()) {
    return false
  }

  // Check modifiers
  const ctrlOrMeta = shortcut.ctrlKey || shortcut.metaKey
  const eventCtrlOrMeta = event.ctrlKey || event.metaKey

  if (ctrlOrMeta && !eventCtrlOrMeta) return false
  if (!ctrlOrMeta && eventCtrlOrMeta) return false

  if (shortcut.shiftKey && !event.shiftKey) return false
  if (!shortcut.shiftKey && event.shiftKey) return false

  if (shortcut.altKey && !event.altKey) return false
  if (!shortcut.altKey && event.altKey) return false

  return true
}

/**
 * Hook for managing shortcut help/documentation
 * 
 * @param shortcuts - Array of shortcuts to document
 * @returns Object with categorized shortcuts for help display
 */
export function useShortcutHelp(shortcuts: KeyboardShortcutConfig[]) {
  const categorizedShortcuts = shortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || "General"
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push({
      ...shortcut,
      display: useShortcutDisplay(shortcut),
    })
    return acc
  }, {} as Record<string, Array<KeyboardShortcutConfig & { display: string }>>)

  return categorizedShortcuts
}