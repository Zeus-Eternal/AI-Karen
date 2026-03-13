import { beforeAll, afterEach, afterAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'

// Setup localStorage mock
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem(key: string) {
      return store[key] || null
    },
    setItem(key: string, value: string) {
      store[key] = value.toString()
    },
    removeItem(key: string) {
      delete store[key]
    },
    clear() {
      store = {}
    },
    get length() {
      return Object.keys(store).length
    },
    key(index: number) {
      return Object.keys(store)[index] || null
    }
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Setup fetch mock
global.fetch = vi.fn()

// Setup environment variables for tests
Object.defineProperty(process, 'env', {
  value: {
    ...process.env,
    NODE_ENV: 'test',
    NEXT_PUBLIC_KAREN_BACKEND_URL: 'http://localhost:8000',
    KAREN_BACKEND_URL: 'http://localhost:8000',
    NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES: 'false',
    NEXT_PUBLIC_ENABLE_DEVELOPER_TOOLS: 'false',
    NEXT_PUBLIC_DEBUG_LOGGING: 'false',
    KAREN_ENABLE_SERVICE_WORKER: 'false',
    KAREN_ENABLE_PERFORMANCE_MONITORING: 'true',
    KAREN_ENABLE_HEALTH_CHECKS: 'true',
  },
  writable: true
})

// Cleanup after each test
afterEach(() => {
  cleanup()
  localStorageMock.clear()
  vi.clearAllMocks()
})

// Setup global error handler
beforeAll(() => {
  // Suppress console errors in tests unless debugging
  if (!process.env.DEBUG_TESTS) {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  }
})

afterAll(() => {
  // Restore console methods
  vi.restoreAllMocks()
})