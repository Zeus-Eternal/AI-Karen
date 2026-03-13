'use client'

import { FormEvent, useEffect, useState } from 'react'
import apiClient from '@/lib/api/client'
import { ChatInterface } from './ChatInterface'

export function AppShell() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendHealth, setBackendHealth] = useState<'unknown' | 'healthy' | 'degraded' | 'offline'>('unknown')

  useEffect(() => {
    const initialize = async () => {
      try {
        await apiClient.healthCheck()
        setBackendHealth('healthy')
      } catch {
        setBackendHealth('offline')
      }

      const token = apiClient.getAuthToken()
      if (!token) {
        setIsCheckingAuth(false)
        return
      }

      const user = await apiClient.getCurrentUser()
      if (user) {
        setIsAuthenticated(true)
      } else {
        apiClient.clearAuthToken()
      }

      setIsCheckingAuth(false)
    }

    initialize()
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setIsLoggingIn(true)

    try {
      await apiClient.login(username, password)
      setIsAuthenticated(true)
      setPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setIsLoggingIn(false)
    }
  }

  if (isCheckingAuth) {
    return <div className="min-h-screen flex items-center justify-center">Checking authentication…</div>
  }

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
        <form onSubmit={handleSubmit} className="w-full max-w-md rounded-xl bg-white shadow p-6 space-y-4">
          <h1 className="text-2xl font-semibold text-gray-900">Sign in to AI-Karen</h1>
          <p className="text-sm text-gray-600">Backend: {apiClient.getBackendUrl()}</p>
          <p className="text-sm text-gray-600">Status: {backendHealth}</p>

          <label className="block text-sm font-medium text-gray-700">
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2"
              autoComplete="username"
              required
            />
          </label>

          <label className="block text-sm font-medium text-gray-700">
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2"
              autoComplete="current-password"
              required
            />
          </label>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={isLoggingIn}
            className="w-full bg-gray-900 text-white rounded-lg px-4 py-2 disabled:opacity-60"
          >
            {isLoggingIn ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </main>
    )
  }

  return <ChatInterface />
}
