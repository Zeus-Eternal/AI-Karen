import { renderHook } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { 
  useKeyboardShortcuts, 
  useKeyboardShortcut, 
  useCommonShortcuts,
  useShortcutDisplay 
} from "../use-keyboard-shortcuts"

// Mock document
const mockAddEventListener = vi.fn()
const mockRemoveEventListener = vi.fn()

beforeEach(() => {
  Object.defineProperty(global, "document", {
    value: {
      addEventListener: mockAddEventListener,
      removeEventListener: mockRemoveEventListener,
    },
    writable: true,
  })
  
  // Mock navigator for shortcut display
  Object.defineProperty(global, "navigator", {
    value: {
      platform: "MacIntel",
    },
    writable: true,
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

describe("useKeyboardShortcuts", () => {
  it("should add event listener when enabled", () => {
    const handler = vi.fn()
    const shortcuts = [
      {
        key: "s",
        ctrlKey: true,
        handler,
      },
    ]

    renderHook(() => useKeyboardShortcuts(shortcuts, true))

    expect(mockAddEventListener).toHaveBeenCalledWith("keydown", expect.any(Function))
  })

  it("should remove event listener on unmount", () => {
    const handler = vi.fn()
    const shortcuts = [
      {
        key: "s",
        ctrlKey: true,
        handler,
      },
    ]

    const { unmount } = renderHook(() => useKeyboardShortcuts(shortcuts, true))
    
    unmount()

    expect(mockRemoveEventListener).toHaveBeenCalledWith("keydown", expect.any(Function))
  })

  it("should not add event listener when disabled", () => {
    const handler = vi.fn()
    const shortcuts = [
      {
        key: "s",
        ctrlKey: true,
        handler,
      },
    ]

    renderHook(() => useKeyboardShortcuts(shortcuts, false))

    expect(mockAddEventListener).not.toHaveBeenCalled()
  })

  it("should handle keyboard events correctly", () => {
    const handler = vi.fn()
    const shortcuts = [
      {
        key: "s",
        ctrlKey: true,
        handler,
      },
    ]

    let keydownHandler: (event: KeyboardEvent) => void

    mockAddEventListener.mockImplementation((event, callback) => {
      if (event === "keydown") {
        keydownHandler = callback
      }
    })

    renderHook(() => useKeyboardShortcuts(shortcuts, true))

    // Simulate Ctrl+S
    const event = new KeyboardEvent("keydown", {
      key: "s",
      ctrlKey: true,
    })
    
    Object.defineProperty(event, "preventDefault", {
      value: vi.fn(),
      writable: true,
    })

    keydownHandler!(event)

    expect(handler).toHaveBeenCalledWith(event)
    expect(event.preventDefault).toHaveBeenCalled()
  })
})

describe("useKeyboardShortcut", () => {
  it("should handle single shortcut", () => {
    const handler = vi.fn()
    const shortcut = {
      key: "Escape",
    }

    renderHook(() => useKeyboardShortcut(shortcut, handler, true))

    expect(mockAddEventListener).toHaveBeenCalledWith("keydown", expect.any(Function))
  })
})

describe("useCommonShortcuts", () => {
  it("should register common shortcuts", () => {
    const handlers = {
      save: vi.fn(),
      copy: vi.fn(),
      paste: vi.fn(),
      undo: vi.fn(),
    }

    renderHook(() => useCommonShortcuts(handlers, true))

    expect(mockAddEventListener).toHaveBeenCalledWith("keydown", expect.any(Function))
  })

  it("should handle save shortcut", () => {
    const saveHandler = vi.fn()
    const handlers = { save: saveHandler }

    let keydownHandler: (event: KeyboardEvent) => void

    mockAddEventListener.mockImplementation((event, callback) => {
      if (event === "keydown") {
        keydownHandler = callback
      }
    })

    renderHook(() => useCommonShortcuts(handlers, true))

    // Simulate Ctrl+S (or Cmd+S on Mac)
    const event = new KeyboardEvent("keydown", {
      key: "s",
      metaKey: true, // Mac
    })
    
    Object.defineProperty(event, "preventDefault", {
      value: vi.fn(),
      writable: true,
    })

    keydownHandler!(event)

    expect(saveHandler).toHaveBeenCalledWith(event)
  })
})

describe("useShortcutDisplay", () => {
  it("should format shortcuts for Mac", () => {
    Object.defineProperty(global, "navigator", {
      value: {
        platform: "MacIntel",
      },
      writable: true,
    })

    const { result } = renderHook(() => 
      useShortcutDisplay({
        key: "s",
        metaKey: true,
        shiftKey: true,
      })
    )

    expect(result.current).toBe("⌘⇧S")
  })

  it("should format shortcuts for Windows/Linux", () => {
    Object.defineProperty(global, "navigator", {
      value: {
        platform: "Win32",
      },
      writable: true,
    })

    const { result } = renderHook(() => 
      useShortcutDisplay({
        key: "s",
        ctrlKey: true,
        altKey: true,
      })
    )

    expect(result.current).toBe("Ctrl+Alt+S")
  })

  it("should format special keys", () => {
    const { result } = renderHook(() => 
      useShortcutDisplay({
        key: "ArrowUp",
      })
    )

    expect(result.current).toBe("↑")
  })

  it("should format escape key", () => {
    const { result } = renderHook(() => 
      useShortcutDisplay({
        key: "Escape",
      })
    )

    expect(result.current).toBe("Esc")
  })
})