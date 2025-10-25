import { renderHook, act } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { useLocalStorage, useSessionStorage, usePersistentUIState } from "../use-local-storage"

// Mock localStorage and sessionStorage
const mockStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: mockStorage,
    writable: true,
  })
  Object.defineProperty(window, "sessionStorage", {
    value: mockStorage,
    writable: true,
  })
  
  // Mock dispatchEvent
  Object.defineProperty(window, "dispatchEvent", {
    value: vi.fn(),
    writable: true,
  })
  
  vi.clearAllMocks()
})

afterEach(() => {
  vi.clearAllMocks()
})

describe("useLocalStorage", () => {
  it("should return initial value when localStorage is empty", () => {
    mockStorage.getItem.mockReturnValue(null)
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    expect(result.current[0]).toBe("initial")
    expect(mockStorage.getItem).toHaveBeenCalledWith("test-key")
  })

  it("should return stored value when localStorage has data", () => {
    mockStorage.getItem.mockReturnValue(JSON.stringify("stored-value"))
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    expect(result.current[0]).toBe("stored-value")
  })

  it("should update localStorage when value changes", () => {
    mockStorage.getItem.mockReturnValue(null)
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    act(() => {
      result.current[1]("new-value")
    })
    
    expect(result.current[0]).toBe("new-value")
    expect(mockStorage.setItem).toHaveBeenCalledWith("test-key", JSON.stringify("new-value"))
    expect(window.dispatchEvent).toHaveBeenCalled()
  })

  it("should handle function updates", () => {
    mockStorage.getItem.mockReturnValue(JSON.stringify("initial"))
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    act(() => {
      result.current[1]((prev) => prev + "-updated")
    })
    
    expect(result.current[0]).toBe("initial-updated")
    expect(mockStorage.setItem).toHaveBeenCalledWith("test-key", JSON.stringify("initial-updated"))
  })

  it("should remove value when removeValue is called", () => {
    mockStorage.getItem.mockReturnValue(JSON.stringify("stored"))
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    act(() => {
      result.current[2]() // removeValue
    })
    
    expect(result.current[0]).toBe("initial")
    expect(mockStorage.removeItem).toHaveBeenCalledWith("test-key")
  })

  it("should handle JSON parse errors gracefully", () => {
    mockStorage.getItem.mockReturnValue("invalid-json")
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {})
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    expect(result.current[0]).toBe("initial")
    expect(consoleSpy).toHaveBeenCalled()
    
    consoleSpy.mockRestore()
  })

  it("should handle localStorage setItem errors gracefully", () => {
    mockStorage.getItem.mockReturnValue(null)
    mockStorage.setItem.mockImplementation(() => {
      throw new Error("Storage quota exceeded")
    })
    const consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {})
    
    const { result } = renderHook(() => useLocalStorage("test-key", "initial"))
    
    act(() => {
      result.current[1]("new-value")
    })
    
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })
})

describe("useSessionStorage", () => {
  it("should work with sessionStorage", () => {
    mockStorage.getItem.mockReturnValue(null)
    
    const { result } = renderHook(() => useSessionStorage("session-key", "initial"))
    
    expect(result.current[0]).toBe("initial")
    
    act(() => {
      result.current[1]("session-value")
    })
    
    expect(result.current[0]).toBe("session-value")
    expect(mockStorage.setItem).toHaveBeenCalledWith("session-key", JSON.stringify("session-value"))
  })
})

describe("usePersistentUIState", () => {
  beforeEach(() => {
    mockStorage.getItem.mockReturnValue(null)
  })

  it("should provide UI state management", () => {
    const { result } = renderHook(() => usePersistentUIState())
    
    expect(result.current.sidebar.collapsed).toBe(false)
    expect(result.current.theme.current).toBe("system")
    expect(result.current.rightPanel.view).toBe("dashboard")
    expect(result.current.accessibility.reducedMotion).toBe(false)
  })

  it("should update sidebar state", () => {
    const { result } = renderHook(() => usePersistentUIState())
    
    act(() => {
      result.current.sidebar.setCollapsed(true)
    })
    
    expect(result.current.sidebar.collapsed).toBe(true)
    expect(mockStorage.setItem).toHaveBeenCalledWith("ui:sidebar-collapsed", "true")
  })

  it("should update theme state", () => {
    const { result } = renderHook(() => usePersistentUIState())
    
    act(() => {
      result.current.theme.set("dark")
    })
    
    expect(result.current.theme.current).toBe("dark")
    expect(mockStorage.setItem).toHaveBeenCalledWith("ui:theme", JSON.stringify("dark"))
  })

  it("should update accessibility settings", () => {
    const { result } = renderHook(() => usePersistentUIState())
    
    act(() => {
      result.current.accessibility.setReducedMotion(true)
      result.current.accessibility.setFontSize("lg")
    })
    
    expect(result.current.accessibility.reducedMotion).toBe(true)
    expect(result.current.accessibility.fontSize).toBe("lg")
  })
})