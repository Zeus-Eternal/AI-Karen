import { renderHook } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { useMediaQuery, useMediaQueries, useBreakpoint, useCurrentBreakpoint } from "../use-media-query"

// Mock matchMedia
const mockMatchMedia = vi.fn()

beforeEach(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: mockMatchMedia,
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

describe("useMediaQuery", () => {
  it("should return false initially when matchMedia is not supported", () => {
    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"))
    expect(result.current).toBe(false)
  })

  it("should return true when media query matches", () => {
    mockMatchMedia.mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"))
    expect(result.current).toBe(true)
  })

  it("should call matchMedia with correct query", () => {
    const query = "(min-width: 768px)"
    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    renderHook(() => useMediaQuery(query))
    expect(mockMatchMedia).toHaveBeenCalledWith(query)
  })

  it("should add and remove event listeners", () => {
    const addEventListener = vi.fn()
    const removeEventListener = vi.fn()
    
    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener,
      removeEventListener,
    })

    const { unmount } = renderHook(() => useMediaQuery("(min-width: 768px)"))
    
    expect(addEventListener).toHaveBeenCalledWith("change", expect.any(Function))
    
    unmount()
    expect(removeEventListener).toHaveBeenCalledWith("change", expect.any(Function))
  })
})

describe("useMediaQueries", () => {
  it("should handle multiple media queries", () => {
    mockMatchMedia
      .mockReturnValueOnce({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })
      .mockReturnValueOnce({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })

    const queries = {
      mobile: "(max-width: 767px)",
      desktop: "(min-width: 768px)",
    }

    const { result } = renderHook(() => useMediaQueries(queries))
    
    expect(result.current.mobile).toBe(true)
    expect(result.current.desktop).toBe(false)
  })
})

describe("useBreakpoint", () => {
  it("should provide breakpoint hooks", () => {
    mockMatchMedia.mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    const { result: mobileResult } = renderHook(() => useBreakpoint.mobile())
    const { result: desktopResult } = renderHook(() => useBreakpoint.desktop())
    
    expect(mobileResult.current).toBe(true)
    expect(desktopResult.current).toBe(true)
  })
})

describe("useCurrentBreakpoint", () => {
  it("should return correct breakpoint", () => {
    // Mock all breakpoints as false except md
    mockMatchMedia
      .mockReturnValueOnce({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) // 2xl
      .mockReturnValueOnce({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) // xl
      .mockReturnValueOnce({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }) // lg
      .mockReturnValueOnce({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })  // md
      .mockReturnValueOnce({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })  // sm

    const { result } = renderHook(() => useCurrentBreakpoint())
    expect(result.current).toBe("md")
  })

  it("should return xs when no breakpoints match", () => {
    // Mock all breakpoints as false
    mockMatchMedia.mockReturnValue({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    const { result } = renderHook(() => useCurrentBreakpoint())
    expect(result.current).toBe("xs")
  })
})