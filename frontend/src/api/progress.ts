import { apiClient, unwrap } from './client'
import type { ProgressResponse, SessionSummaryResponse } from '../types'

export const progressApi = {
  myProgress: async (): Promise<ProgressResponse> =>
    unwrap(await apiClient.get('/users/me/progress')),

  mySessions: async (limit = 20, offset = 0): Promise<SessionSummaryResponse[]> =>
    unwrap(await apiClient.get('/users/me/sessions', { params: { limit, offset } })),
}
