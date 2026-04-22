import { apiClient, unwrap } from './client'
import type { LoginRequest, RegisterRequest, TokenResponse, UserResponse } from '../types'

export const authApi = {
  register: async (body: RegisterRequest): Promise<UserResponse> =>
    unwrap(await apiClient.post('/auth/register', body)),

  login: async (body: LoginRequest): Promise<TokenResponse> =>
    unwrap(await apiClient.post('/auth/login', body)),

  refresh: async (refresh_token: string): Promise<TokenResponse> =>
    unwrap(await apiClient.post('/auth/refresh', { refresh_token })),

  logout: async (): Promise<void> => {
    await apiClient.delete('/auth/logout')
  },

  me: async (): Promise<UserResponse> =>
    unwrap(await apiClient.get('/auth/me')),
}
