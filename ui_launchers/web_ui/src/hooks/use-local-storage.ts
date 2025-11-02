"use client"
import { useState, useEffect, useCallback } from "react"
/**
 * Hook for managing localStorage with React state synchronization
 * 
 * @param key - The localStorage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns [value, setValue, removeValue] tuple
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // State to store our value
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === "undefined") {
      return initialValue
    }
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      return initialValue
    }
  })
  // Return a wrapped version of useState's setter function that persists the new value to localStorage
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        // Allow value to be a function so we have the same API as useState
        const valueToStore = value instanceof Function ? value(storedValue) : value
        // Save state
        setStoredValue(valueToStore)
        // Save to localStorage
        if (typeof window !== "undefined") {
          window.localStorage.setItem(key, JSON.stringify(valueToStore))
          // Dispatch custom event to sync across tabs/components
          window.dispatchEvent(
            new CustomEvent("localStorage", {
              detail: { key, value: valueToStore },
            })
          )
        }
      } catch (error) {
      }
    },
    [key, storedValue]
  )
  // Function to remove the value from localStorage
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue)
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(key)
        // Dispatch custom event to sync across tabs/components
        window.dispatchEvent(
          new CustomEvent("localStorage", {
            detail: { key, value: undefined },
          })
        )
      }
    } catch (error) {
    }
  }, [key, initialValue])
  // Listen for changes in localStorage from other tabs/windows
  useEffect(() => {
    if (typeof window === "undefined") {
      return
    }
    const handleStorageChange = (e: StorageEvent | CustomEvent) => {
      if ("key" in e && e.key === key) {
        try {
          const newValue = e.newValue ? JSON.parse(e.newValue) : initialValue
          setStoredValue(newValue)
        } catch (error) {
        }
      } else if ("detail" in e && e.detail?.key === key) {
        // Handle custom event for same-tab synchronization
        setStoredValue(e.detail.value ?? initialValue)
      }
    }
    // Listen for storage events (cross-tab)
    window.addEventListener("storage", handleStorageChange)
    // Listen for custom events (same-tab)
    window.addEventListener("localStorage", handleStorageChange as EventListener)
    return () => {
      window.removeEventListener("storage", handleStorageChange)
      window.removeEventListener("localStorage", handleStorageChange as EventListener)
    }
  }, [key, initialValue])
  return [storedValue, setValue, removeValue]
}
/**
 * Hook for managing sessionStorage with React state synchronization
 * 
 * @param key - The sessionStorage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns [value, setValue, removeValue] tuple
 */
export function useSessionStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === "undefined") {
      return initialValue
    }
    try {
      const item = window.sessionStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      return initialValue
    }
  })
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value
        setStoredValue(valueToStore)
        if (typeof window !== "undefined") {
          window.sessionStorage.setItem(key, JSON.stringify(valueToStore))
        }
      } catch (error) {
      }
    },
    [key, storedValue]
  )
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue)
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(key)
      }
    } catch (error) {
    }
  }, [key, initialValue])
  return [storedValue, setValue, removeValue]
}
/**
 * Hook for managing persistent UI state with localStorage
 * Provides common UI state management patterns
 */
export function usePersistentUIState() {
  const [sidebarCollapsed, setSidebarCollapsed] = useLocalStorage("ui:sidebar-collapsed", false)
  const [theme, setTheme] = useLocalStorage<"light" | "dark" | "system">("ui:theme", "system")
  const [rightPanelView, setRightPanelView] = useLocalStorage("ui:right-panel-view", "dashboard")
  const [reducedMotion, setReducedMotion] = useLocalStorage("ui:reduced-motion", false)
  const [highContrast, setHighContrast] = useLocalStorage("ui:high-contrast", false)
  const [fontSize, setFontSize] = useLocalStorage<"sm" | "md" | "lg">("ui:font-size", "md")
  return {
    sidebar: {
      collapsed: sidebarCollapsed,
      setCollapsed: setSidebarCollapsed,
    },
    theme: {
      current: theme,
      set: setTheme,
    },
    rightPanel: {
      view: rightPanelView,
      setView: setRightPanelView,
    },
    accessibility: {
      reducedMotion,
      setReducedMotion,
      highContrast,
      setHighContrast,
      fontSize,
      setFontSize,
    },
  }
}
/**
 * Hook for managing form state persistence
 * Useful for preserving form data across page refreshes
 */
export function usePersistentForm<T extends Record<string, any>>(
  formId: string,
  initialValues: T,
  options: {
    clearOnSubmit?: boolean
    storage?: "localStorage" | "sessionStorage"
  } = {}
) {
  const { clearOnSubmit = true, storage = "sessionStorage" } = options
  const storageKey = `form:${formId}`
  const [values, setValues] = storage === "localStorage" 
    ? useLocalStorage(storageKey, initialValues)
    : useSessionStorage(storageKey, initialValues)
  const updateField = useCallback(
    (field: keyof T, value: T[keyof T]) => {
      setValues((prev) => ({ ...prev, [field]: value }))
    },
    [setValues]
  )
  const updateFields = useCallback(
    (updates: Partial<T>) => {
      setValues((prev) => ({ ...prev, ...updates }))
    },
    [setValues]
  )
  const resetForm = useCallback(() => {
    setValues(initialValues)
  }, [setValues, initialValues])
  const clearForm = useCallback(() => {
    if (storage === "localStorage") {
      const [, , removeValue] = useLocalStorage(storageKey, initialValues)
      removeValue()
    } else {
      const [, , removeValue] = useSessionStorage(storageKey, initialValues)
      removeValue()
    }
  }, [storageKey, initialValues, storage])
  return {
    values,
    setValues,
    updateField,
    updateFields,
    resetForm,
    clearForm,
  }
}
