"use client"

import { useState, useEffect } from "react"

/**
 * Hook to track media query matches
 * 
 * @param query - The media query string to track
 * @returns boolean indicating if the media query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    // Check if we're in a browser environment
    if (typeof window === "undefined") {
      return
    }

    const mediaQuery = window.matchMedia(query)
    
    // Set initial value
    setMatches(mediaQuery.matches)

    // Listen for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    // Add event listener
    mediaQuery.addEventListener("change", handleChange)

    // Cleanup
    return () => {
      mediaQuery.removeEventListener("change", handleChange)
    }
  }, [query])

  return matches
}

/**
 * Hook to track multiple media queries
 * 
 * @param queries - Object with keys as names and values as media query strings
 * @returns Object with same keys and boolean values indicating matches
 */
export function useMediaQueries<T extends Record<string, string>>(
  queries: T
): Record<keyof T, boolean> {
  const [matches, setMatches] = useState<Record<keyof T, boolean>>(() => {
    const initialState = {} as Record<keyof T, boolean>
    Object.keys(queries).forEach((key) => {
      initialState[key as keyof T] = false
    })
    return initialState
  })

  useEffect(() => {
    if (typeof window === "undefined") {
      return
    }

    const mediaQueries = Object.entries(queries).map(([key, query]) => ({
      key: key as keyof T,
      mediaQuery: window.matchMedia(query as string),
    }))

    // Set initial values
    const initialMatches = {} as Record<keyof T, boolean>
    mediaQueries.forEach(({ key, mediaQuery }) => {
      initialMatches[key] = mediaQuery.matches
    })
    setMatches(initialMatches)

    // Create handlers
    const handlers = mediaQueries.map(({ key, mediaQuery }) => {
      const handler = (event: MediaQueryListEvent) => {
        setMatches((prev) => ({
          ...prev,
          [key]: event.matches,
        }))
      }
      mediaQuery.addEventListener("change", handler)
      return { mediaQuery, handler }
    })

    // Cleanup
    return () => {
      handlers.forEach(({ mediaQuery, handler }) => {
        mediaQuery.removeEventListener("change", handler)
      })
    }
  }, [queries])

  return matches
}

/**
 * Predefined breakpoint hooks for common responsive design patterns
 */
export const useBreakpoint = {
  /**
   * Hook to check if screen is mobile size (< 640px)
   */
  mobile: () => useMediaQuery("(max-width: 639px)"),
  
  /**
   * Hook to check if screen is tablet size (640px - 1023px)
   */
  tablet: () => useMediaQuery("(min-width: 640px) and (max-width: 1023px)"),
  
  /**
   * Hook to check if screen is desktop size (>= 1024px)
   */
  desktop: () => useMediaQuery("(min-width: 1024px)"),
  
  /**
   * Hook to check if screen is small (>= 640px)
   */
  sm: () => useMediaQuery("(min-width: 640px)"),
  
  /**
   * Hook to check if screen is medium (>= 768px)
   */
  md: () => useMediaQuery("(min-width: 768px)"),
  
  /**
   * Hook to check if screen is large (>= 1024px)
   */
  lg: () => useMediaQuery("(min-width: 1024px)"),
  
  /**
   * Hook to check if screen is extra large (>= 1280px)
   */
  xl: () => useMediaQuery("(min-width: 1280px)"),
  
  /**
   * Hook to check if screen is 2x extra large (>= 1536px)
   */
  "2xl": () => useMediaQuery("(min-width: 1536px)"),
}

/**
 * Hook to get current breakpoint name
 * 
 * @returns string indicating the current breakpoint
 */
export function useCurrentBreakpoint(): "xs" | "sm" | "md" | "lg" | "xl" | "2xl" {
  const breakpoints = useMediaQueries({
    "2xl": "(min-width: 1536px)",
    xl: "(min-width: 1280px)",
    lg: "(min-width: 1024px)",
    md: "(min-width: 768px)",
    sm: "(min-width: 640px)",
  })

  if (breakpoints["2xl"]) return "2xl"
  if (breakpoints.xl) return "xl"
  if (breakpoints.lg) return "lg"
  if (breakpoints.md) return "md"
  if (breakpoints.sm) return "sm"
  return "xs"
}

/**
 * Hook to check device capabilities
 */
export const useDeviceCapabilities = {
  /**
   * Hook to check if device supports hover
   */
  hover: () => useMediaQuery("(hover: hover)"),
  
  /**
   * Hook to check if device has a pointer (mouse)
   */
  pointer: () => useMediaQuery("(pointer: fine)"),
  
  /**
   * Hook to check if device is touch-capable
   */
  touch: () => useMediaQuery("(pointer: coarse)"),
  
  /**
   * Hook to check if user prefers dark color scheme
   */
  darkMode: () => useMediaQuery("(prefers-color-scheme: dark)"),
  
  /**
   * Hook to check if user prefers light color scheme
   */
  lightMode: () => useMediaQuery("(prefers-color-scheme: light)"),
  
  /**
   * Hook to check if user prefers high contrast
   */
  highContrast: () => useMediaQuery("(prefers-contrast: high)"),
}