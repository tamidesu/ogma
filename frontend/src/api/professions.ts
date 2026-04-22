import { apiClient, unwrap } from './client'
import type { ProfessionResponse, ScenarioSummaryResponse } from '../types'

export const professionsApi = {
  list: async (): Promise<ProfessionResponse[]> =>
    unwrap(await apiClient.get('/professions')),

  get: async (professionId: string): Promise<ProfessionResponse> =>
    unwrap(await apiClient.get(`/professions/${professionId}`)),

  scenarios: async (professionId: string): Promise<ScenarioSummaryResponse[]> =>
    unwrap(await apiClient.get(`/professions/${professionId}/scenarios`)),
}
