import { apiClient, unwrap } from './client'
import type {
  CreateSessionRequest,
  DecisionHistoryItem,
  DecisionResponse,
  FeedbackPollResponse,
  MakeDecisionRequest,
  SessionResponse,
} from '../types'

export const sessionsApi = {
  create: async (body: CreateSessionRequest): Promise<SessionResponse> =>
    unwrap(await apiClient.post('/sessions', body)),

  get: async (sessionId: string): Promise<SessionResponse> =>
    unwrap(await apiClient.get(`/sessions/${sessionId}`)),

  decide: async (sessionId: string, body: MakeDecisionRequest): Promise<DecisionResponse> =>
    unwrap(await apiClient.post(`/sessions/${sessionId}/decisions`, body)),

  pause: async (sessionId: string): Promise<Record<string, unknown>> =>
    unwrap(await apiClient.post(`/sessions/${sessionId}/pause`)),

  remove: async (sessionId: string): Promise<void> => {
    await apiClient.delete(`/sessions/${sessionId}`)
  },

  history: async (sessionId: string): Promise<DecisionHistoryItem[]> =>
    unwrap(await apiClient.get(`/sessions/${sessionId}/history`)),

  getFeedback: async (sessionId: string, decisionId: string): Promise<FeedbackPollResponse> =>
    unwrap(await apiClient.get(`/sessions/${sessionId}/decisions/${decisionId}/feedback`)),

  streamFeedback: (sessionId: string, decisionId: string): EventSource => {
    const token = localStorage.getItem('access_token') ?? ''
    // EventSource doesn't support custom headers natively — pass token as query param
    return new EventSource(
      `/api/v1/sessions/${sessionId}/decisions/${decisionId}/feedback/stream?token=${token}`,
    )
  },
}
