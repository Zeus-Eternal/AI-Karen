/**
 * API Client Configuration and Base Client
 * Handles all communication with the AI-Karen backend
 */

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000'
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10)
const API_KEY = process.env.NEXT_PUBLIC_API_KEY

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface AuthUser {
  id: string
  username: string
  email?: string
  roles?: string[]
}

/**
 * Get authentication token from localStorage or cookies
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null

  const token = localStorage.getItem('auth_token')
  if (token) return token

  const cookies = document.cookie.split(';')
  const authCookie = cookies.find((cookie) => cookie.trim().startsWith('auth_token='))
  return authCookie ? decodeURIComponent(authCookie.split('=')[1] || '') : null
}

function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return

  localStorage.setItem('auth_token', token)
  document.cookie = `auth_token=${encodeURIComponent(token)}; path=/; SameSite=Lax`
}

function clearAuthToken(): void {
  if (typeof window === 'undefined') return

  localStorage.removeItem('auth_token')
  document.cookie = 'auth_token=; Max-Age=0; path=/; SameSite=Lax'
}

/**
 * Base API client with error handling and authentication
 */
async function apiRequest(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const url = `${BACKEND_URL}${endpoint}`
  const token = getAuthToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  } else if (API_KEY) {
    headers.Authorization = `Bearer ${API_KEY}`
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT)

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let errorDetails: unknown
      try {
        errorDetails = await response.json()
      } catch {
        errorDetails = await response.text()
      }

      const message =
        typeof errorDetails === 'object' &&
        errorDetails !== null &&
        'message' in errorDetails &&
        typeof (errorDetails as { message?: unknown }).message === 'string'
          ? (errorDetails as { message: string }).message
          : `HTTP ${response.status}: ${response.statusText}`

      throw new ApiError(message, response.status, errorDetails)
    }

    return response
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof ApiError) throw error

    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('Request timeout', 408)
    }

    throw new ApiError(error instanceof Error ? error.message : 'Network error', 0)
  }
}

export const apiClient = {
  getBackendUrl(): string {
    return BACKEND_URL
  },

  getAuthToken,
  setAuthToken,
  clearAuthToken,

  async login(username: string, password: string): Promise<{ token: string; user?: AuthUser }> {
    const response = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })

    const data = (await response.json()) as {
      token?: string
      access_token?: string
      user?: AuthUser
    }

    const token = data.token || data.access_token
    if (!token) {
      throw new ApiError('Login response missing token', 500, data)
    }

    setAuthToken(token)
    return { token, user: data.user }
  },

  async getCurrentUser(): Promise<AuthUser | null> {
    try {
      const response = await apiRequest('/api/auth/me', { method: 'GET' })
      return (await response.json()) as AuthUser
    } catch {
      return null
    }
  },

  async healthCheck(): Promise<Record<string, unknown>> {
    const response = await apiRequest('/api/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
    return (await response.json()) as Record<string, unknown>
  },

  async sendMessage(
    conversationId: string,
    message: string,
    options?: {
      agentId?: string
      executionMode?: 'native' | 'langgraph' | 'deepagents' | 'auto'
      context?: Record<string, unknown>
    }
  ): Promise<Response> {
    return apiRequest('/api/chat/send', {
      method: 'POST',
      body: JSON.stringify({
        conversationId,
        message,
        ...options,
      }),
    })
  },

  async streamMessage(
    conversationId: string,
    message: string,
    options?: {
      agentId?: string
      executionMode?: 'native' | 'langgraph' | 'deepagents' | 'auto'
      onChunk?: (chunk: string) => void
      onMetadata?: (metadata: Record<string, unknown>) => void
      onError?: (error: string) => void
      onDone?: () => void
      signal?: AbortSignal
    }
  ): Promise<void> {
    const token = getAuthToken()
    const url = new URL(`${BACKEND_URL}/api/chat/send`)

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : API_KEY ? { Authorization: `Bearer ${API_KEY}` } : {}),
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        conversationId,
        message,
        stream: true,
        ...options,
      }),
      signal: options?.signal,
    })

    if (!response.ok) {
      throw new ApiError(`HTTP ${response.status}: ${response.statusText}`, response.status)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new ApiError('No response body', 500)
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        options?.onDone?.()
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue

        const data = line.slice(6).trim()
        if (data === '[DONE]') {
          options?.onDone?.()
          return
        }

        try {
          const parsed = JSON.parse(data) as {
            type?: string
            content?: string
            metadata?: Record<string, unknown>
            error?: string
          }

          if (parsed.type === 'token' && parsed.content) {
            options?.onChunk?.(parsed.content)
          } else if (parsed.type === 'metadata') {
            options?.onMetadata?.(parsed.metadata || {})
          } else if (parsed.type === 'error') {
            options?.onError?.(parsed.error || 'Unknown stream error')
          }
        } catch {
          // Ignore invalid JSON
        }
      }
    }
  },

  async getConversations(): Promise<Response> {
    return apiRequest('/api/conversations', {
      method: 'GET',
    })
  },

  async getConversation(conversationId: string): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: 'GET',
    })
  },

  async createConversation(title?: string): Promise<Response> {
    return apiRequest('/api/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    })
  },

  async updateConversation(
    conversationId: string,
    updates: { title?: string; tags?: string[] }
  ): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  },

  async deleteConversation(conversationId: string): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: 'DELETE',
    })
  },

  async searchConversations(query: string): Promise<Response> {
    return apiRequest(`/api/conversations/search?q=${encodeURIComponent(query)}`, {
      method: 'GET',
    })
  },

  async getMessages(conversationId: string): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}/messages`, {
      method: 'GET',
    })
  },
}

export default apiClient
