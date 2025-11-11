"use client"

import { useMemo, useSyncExternalStore } from "react"

/**
 * Hook to track media query matches
 * 
 * @param query - The media query string to track
 * @returns boolean indicating if the media query matches
 */
function createMediaQueryStore(query: string) {
  const getSnapshot = () => {
    if (typeof window === "undefined") {
      return false
    }
    return window.matchMedia(query).matches
  }

  const subscribe = (notify: () => void) => {
    if (typeof window === "undefined") {
      return () => undefined
    }

    const mediaQuery = window.matchMedia(query)
    const handler = () => notify()
    mediaQuery.addEventListener("change", handler)

    return () => mediaQuery.removeEventListener("change", handler)
  }

  return { getSnapshot, subscribe }
}

export function useMediaQuery(query: string): boolean {
  const { getSnapshot, subscribe } = useMemo(() => createMediaQueryStore(query), [query])
  return useSyncExternalStore(subscribe, getSnapshot, () => false)
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
  const entries = useMemo(
    () => Object.entries(queries) as Array<[keyof T, string]>,
    [queries]
  )

  const getSnapshot = () => {
    if (typeof window === "undefined") {
      return entries.reduce((acc, [key]) => {
        acc[key] = false
        return acc
      }, {} as Record<keyof T, boolean>)
    }
    return entries.reduce((acc, [key, query]) => {
      acc[key] = window.matchMedia(query).matches
      return acc
    }, {} as Record<keyof T, boolean>)
  }

  const subscribe = (notify: () => void) => {
    if (typeof window === "undefined") {
      return () => undefined
    }

    const unsubscribers = entries.map(([, query]) => {
      const mediaQuery = window.matchMedia(query)
      const handler = () => notify()
      mediaQuery.addEventListener("change", handler)
      return () => mediaQuery.removeEventListener("change", handler)
    })

    return () => unsubscribers.forEach((unsubscribe) => unsubscribe())
  }

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
}

const useBreakpointMobile = () => useMediaQuery("(max-width: 639px)")
const useBreakpointTablet = () =>
  useMediaQuery("(min-width: 640px) and (max-width: 1023px)")
const useBreakpointDesktop = () => useMediaQuery("(min-width: 1024px)")
const useBreakpointSm = () => useMediaQuery("(min-width: 640px)")
const useBreakpointMd = () => useMediaQuery("(min-width: 768px)")
const useBreakpointLg = () => useMediaQuery("(min-width: 1024px)")
const useBreakpointXl = () => useMediaQuery("(min-width: 1280px)")
const useBreakpoint2xl = () => useMediaQuery("(min-width: 1536px)")

/**
 * Predefined breakpoint hooks for common responsive design patterns
 */
export const useBreakpoint = {
  mobile: useBreakpointMobile,
  tablet: useBreakpointTablet,
  desktop: useBreakpointDesktop,
  sm: useBreakpointSm,
  md: useBreakpointMd,
  lg: useBreakpointLg,
  xl: useBreakpointXl,
  "2xl": useBreakpoint2xl,
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

const useDeviceHover = () => useMediaQuery("(hover: hover)")
const useDevicePointer = () => useMediaQuery("(pointer: fine)")
const useDeviceTouch = () => useMediaQuery("(pointer: coarse)")
const useDeviceDarkMode = () =>
  useMediaQuery("(prefers-color-scheme: dark)")
const useDeviceLightMode = () =>
  useMediaQuery("(prefers-color-scheme: light)")
const useDeviceHighContrast = () => useMediaQuery("(prefers-contrast: high)")

/**
 * Hook to check device capabilities
 */
export const useDeviceCapabilities = {
  hover: useDeviceHover,
  pointer: useDevicePointer,
  touch: useDeviceTouch,
  darkMode: useDeviceDarkMode,
  lightMode: useDeviceLightMode,
  highContrast: useDeviceHighContrast,
}
