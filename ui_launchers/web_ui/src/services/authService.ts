import { getKarenBackend, type LoginResult, type CurrentUser } from '@/lib/karen-backend'
import { storeAuthToken, getAuthToken, clearAuthToken } from '@/lib/auth-token'

export class AuthService {
  private backend = getKarenBackend()

  async login(username: string, password: string): Promise<LoginResult | null> {
    try {
      const result = await this.backend.login(username, password)
      storeAuthToken(result.token)
      return result
    } catch (error) {
      console.error('AuthService: login failed', error)
      return null
    }
  }

  async getCurrentUser(): Promise<CurrentUser | null> {
    const token = getAuthToken()
    if (!token) return null
    return await this.backend.getCurrentUser(token)
  }

  async updateCredentials(newUsername?: string, newPassword?: string): Promise<LoginResult | null> {
    const token = getAuthToken()
    if (!token) return null
    try {
      const result = await this.backend.updateCredentials(token, newUsername, newPassword)
      storeAuthToken(result.token)
      return result
    } catch (error) {
      console.error('AuthService: update credentials failed', error)
      return null
    }
  }

  logout() {
    clearAuthToken()
  }
}

let authService: AuthService | null = null
export function getAuthService(): AuthService {
  if (!authService) authService = new AuthService()
  return authService
}
