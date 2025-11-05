import { safeError } from './safe-console'

const STORAGE_KEY = 'kari_api_key'

export function storeApiKey(key: string) {
  try {
    const encoded = btoa(key)
    sessionStorage.setItem(STORAGE_KEY, encoded)
  } catch (err) {
    safeError('Failed to store API key', err)
  }
}

export function getStoredApiKey(): string | null {
  try {
    const val = sessionStorage.getItem(STORAGE_KEY)
    return val ? atob(val) : null
  } catch {
    return null
  }
}
