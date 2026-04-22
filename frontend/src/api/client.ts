import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import type { ResponseEnvelope } from '../types'

const BASE_URL = '/api/v1'

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Inject access token
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Unwrap envelope + handle 401 with refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post<ResponseEnvelope<{ access_token: string; refresh_token: string; token_type: string }>>(
            `${BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken },
          )
          const tokens = res.data.data!
          localStorage.setItem('access_token', tokens.access_token)
          localStorage.setItem('refresh_token', tokens.refresh_token)
          original.headers.Authorization = `Bearer ${tokens.access_token}`
          return apiClient(original)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

export function unwrap<T>(res: AxiosResponse<ResponseEnvelope<T>>): T {
  const envelope = res.data
  if (envelope.errors) throw new Error(envelope.errors.message)
  return envelope.data as T
}
