/**
 * API Client Configuration and Base Client
 * Handles all communication with the AI-Karen backend
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10)

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

/**
 * Get authentication token from localStorage or cookies
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  
  // Check localStorage first
  const token = localStorage.getItem('auth_token')
  if (token) return token
  
  // Check cookies
  const cookies = document.cookie.split(';')
  const authCookie = cookies.find(c => c.trim().startsWith('auth_token='))
  return authCookie?.split('=')[1] || null
}

/**
 * Base API client with error handling and authentication
 */
async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = `${BACKEND_URL}${endpoint}`
  const token = getAuthToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT)

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      let errorDetails
      try {
        errorDetails = await response.json()
      } catch {
        errorDetails = await response.text()
      }

      throw new ApiError(
        errorDetails?.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorDetails
      )
    }

    return response
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof ApiError) throw error
    
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError('Request timeout', 408)
    }

    throw new ApiError(
      error instanceof Error ? error.message : 'Network error',
      0
    )
  }
}

/**
 * API client with typed methods for all endpoints
 */
export const apiClient = {
  /**
   * Send a message to the AI
   */
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

  /**
   * Stream a message response using Server-Sent Events
   */
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
    }
  ): Promise<void> {
    const token = getAuthToken()
    const url = new URL(`${BACKEND_URL}/api/chat/send`)
    
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        conversationId,
        message,
        stream: true,
        ...options,
      }),
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
          const parsed = JSON.parse(data)
          
          if (parsed.type === 'token' && parsed.content) {
            options?.onChunk?.(parsed.content)
          } else if (parsed.type === 'metadata') {
            options?.onMetadata?.(parsed.metadata)
          } else if (parsed.type === 'error') {
            options?.onError?.(parsed.error)
          }
        } catch {
          // Ignore invalid JSON
        }
      }
    }
  },

  /**
   * Get all conversations
   */
  async getConversations(): Promise<Response> {
    return apiRequest('/api/conversations', {
      method: 'GET',
    })
  },

  /**
   * Get a single conversation by ID
   */
  async getConversation(conversationId: string): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: 'GET',
    })
  },

  /**
   * Create a new conversation
   */
  async createConversation(title?: string): Promise<Response> {
    return apiRequest('/api/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    })
  },

  /**
   * Update conversation title or metadata
   */
  async updateConversation(
    conversationId: string,
    updates: { title?: string; tags?: string[] }
  ): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
  },

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: 'DELETE',
    })
  },

  /**
   * Search conversations
   */
  async searchConversations(query: string): Promise<Response> {
    return apiRequest(`/api/conversations/search?q=${encodeURIComponent(query)}`, {
      method: 'GET',
    })
  },

  /**
   * Get messages for a conversation
   */
  async getMessages(conversationId: string): Promise<Response> {
    return apiRequest(`/api/conversations/${conversationId}/messages`, {
      method: 'GET',
    })
  },
}

export default apiClient
