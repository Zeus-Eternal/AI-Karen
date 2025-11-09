const TOKEN_KEY = 'kari_auth_token'

export function storeAuthToken(token: string) {
  try {
    sessionStorage.setItem(TOKEN_KEY, token)
  } catch (err) {
    console.error('[AUTH] Failed to store auth token:', err);
  }
}

export function getAuthToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch (err) {
    console.error('[AUTH] Failed to retrieve auth token:', err);
    return null
  }
}

export function clearAuthToken() {
  try {
    sessionStorage.removeItem(TOKEN_KEY)
  } catch (err) {
    console.error('[AUTH] Failed to clear auth token:', err);
  }
}
