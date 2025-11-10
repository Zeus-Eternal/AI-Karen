import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

type ImportMetaWithEnv = ImportMeta & {
  env?: Record<string, string | undefined>
}

const resolveBaseUrl = (): string => {
  const metaEnv = (import.meta as unknown as ImportMetaWithEnv | undefined)?.env?.VITE_API_URL
  if (metaEnv && metaEnv.length > 0) {
    return metaEnv
  }

  const processEnv = typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_API_URL : undefined
  if (processEnv && processEnv.length > 0) {
    return processEnv
  }

  return 'http://localhost:8000'
}

const BASE_URL = resolveBaseUrl()

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API Types
export interface ChatRequest {
  message: string
  conversation_id?: string
  context?: Record<string, any>
}

export interface ChatResponse {
  response: string
  conversation_id: string
  metadata?: Record<string, any>
}

export interface Plugin {
  id: string
  name: string
  description: string
  enabled: boolean
  version: string
  category: string
}

export interface SystemHealth {
  status: string
  version: string
  uptime: number
  components: Record<string, { status: string; latency?: number }>
}

// API Functions
export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const { data } = await apiClient.post('/api/chat/message', request)
    return data
  },

  getConversations: async (): Promise<any[]> => {
    const { data } = await apiClient.get('/api/chat/conversations')
    return data
  },

  getConversation: async (id: string): Promise<any> => {
    const { data } = await apiClient.get(`/api/chat/conversations/${id}`)
    return data
  },

  deleteConversation: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/chat/conversations/${id}`)
  },
}

export const pluginAPI = {
  list: async (): Promise<Plugin[]> => {
    const { data } = await apiClient.get('/api/plugins')
    return data
  },

  get: async (id: string): Promise<Plugin> => {
    const { data } = await apiClient.get(`/api/plugins/${id}`)
    return data
  },

  toggle: async (id: string, enabled: boolean): Promise<Plugin> => {
    const { data } = await apiClient.patch(`/api/plugins/${id}`, { enabled })
    return data
  },

  execute: async (id: string, payload: any): Promise<any> => {
    const { data } = await apiClient.post(`/api/plugins/${id}/execute`, payload)
    return data
  },
}

export const systemAPI = {
  health: async (): Promise<SystemHealth> => {
    const { data } = await apiClient.get('/api/system/health')
    return data
  },

  metrics: async (): Promise<any> => {
    const { data } = await apiClient.get('/api/system/metrics')
    return data
  },

  settings: async (): Promise<Record<string, any>> => {
    const { data} = await apiClient.get('/api/system/settings')
    return data
  },

  updateSettings: async (settings: Record<string, any>): Promise<void> => {
    await apiClient.put('/api/system/settings', settings)
  },
}

export const analyticsAPI = {
  getStats: async (): Promise<any> => {
    const { data } = await apiClient.get('/api/analytics/stats')
    return data
  },

  getUsage: async (period: string = '7d'): Promise<any> => {
    const { data } = await apiClient.get(`/api/analytics/usage?period=${period}`)
    return data
  },
}

export default apiClient
