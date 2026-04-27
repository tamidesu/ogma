import { apiClient, unwrap } from './client'

// ── Types ──────────────────────────────────────────────────────────────────

export interface BriefSummary {
  id: string
  slug: string
  title: string
  profession_slug: string
  difficulty: number
  estimated_turns: number
  max_turns: number
  locale: string
  npc_display_name: string
  npc_role: string
  initial_suggested_actions: string[]
}

export interface BriefDetail extends BriefSummary {
  case_file_md: string
  npc_definition: NpcDefinition
  initial_world_state: WorldState
}

export interface NpcDefinition {
  id: string
  display_name: string
  role: string
  backstory: string
  personality_traits: Record<string, number>
  initial_emotion: Record<string, number>
  voice_directives: string
  avatar_image_id: string
}

export interface WorldState {
  metrics: Record<string, number>
  flags: Record<string, boolean | string | number>
  time: { elapsed_min: number; current_phase: string }
  diagnosis?: Record<string, unknown>
}

export interface OpenWorldSession {
  session_id: string
  brief_id: string
  brief_slug: string
  title: string
  case_file_md: string
  locale: string
  max_turns: number
  npc: {
    id: string
    display_name: string
    role: string
    initial_emotion: Record<string, number>
    avatar_image_id: string
  }
  initial_world_state: WorldState
  initial_suggested_actions: string[]
  started_at: string
}

// SSE event payloads
export interface IntentEvent {
  verb: string
  target: string
  plausibility: number
  requires_clarification: string | null
  raw_paraphrase: string
}

export interface Citation {
  source: string
  snippet: string
  tag: string
  relevance: number
}

export interface ValidationEvent {
  is_legal: boolean
  is_standard_of_care: boolean
  severity_if_wrong: 'minor' | 'moderate' | 'severe' | 'critical'
  citations: Citation[]
  coach_note: string
  blocks_action: boolean
}

export interface NpcEvent {
  emotion_delta: Record<string, number>
  new_state_label: string
  utterance: string
  body_language: string
  suggested_avatar_id: string
  relationship_delta: number
}

export interface WorldEvent {
  metric_delta: Record<string, number>
  state_set: Record<string, unknown>
  time_advance_min: number
  new_complication: Record<string, unknown> | null
  skill_xp: Array<{ skill: string; xp: number }>
  current_metrics: Record<string, number>
  elapsed_min: number
}

export interface SceneEvent {
  image_id: string
  image_url: string
  alt_text: string
  is_fallback: boolean
  transition: string
}

export interface TerminalEvent {
  is_terminal: boolean
  termination_reason: 'success' | 'failure' | 'timeout'
  final_metrics: Record<string, number>
  total_turns: number
  timeout_resolution: string | null
}

export interface DoneEvent {
  turn_index: number
  latency_ms: number
  turn_id: string | null
}

export type TurnEvent =
  | { type: 'intent'; data: IntentEvent }
  | { type: 'validation'; data: ValidationEvent }
  | { type: 'npc'; data: NpcEvent }
  | { type: 'world'; data: WorldEvent }
  | { type: 'scene'; data: SceneEvent }
  | { type: 'terminal'; data: TerminalEvent }
  | { type: 'done'; data: DoneEvent }
  | { type: 'error'; data: { message: string } }

// ── API ────────────────────────────────────────────────────────────────────

export const brifsApi = {
  list: async (profession_slug: string): Promise<BriefSummary[]> =>
    unwrap(await apiClient.get('/briefs', { params: { profession_slug } })),

  get: async (briefId: string): Promise<BriefDetail> =>
    unwrap(await apiClient.get(`/briefs/${briefId}`)),
}

export const openWorldApi = {
  createSession: async (briefId: string): Promise<OpenWorldSession> =>
    unwrap(await apiClient.post('/open-world/sessions', { brief_id: briefId })),

  getState: async (sessionId: string) =>
    unwrap(await apiClient.get(`/open-world/sessions/${sessionId}/state`)),

  getSuggestedActions: async (sessionId: string): Promise<string[]> =>
    unwrap(await apiClient.get(`/open-world/sessions/${sessionId}/suggested-actions`)),

  /**
   * Stream a turn via SSE. Returns an EventSource.
   * The caller is responsible for closing it when done.
   * Note: we use fetch+ReadableStream since SSE doesn't support POST + custom headers.
   */
  streamTurn: async (
    sessionId: string,
    userText: string,
    locale = 'kk',
    onEvent: (event: TurnEvent) => void,
    onComplete: () => void,
    onError: (err: Error) => void,
  ): Promise<void> => {
    const token = localStorage.getItem('access_token') ?? ''
    const response = await fetch(`/api/v1/open-world/sessions/${sessionId}/turn`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ user_text: userText, locale }),
    })

    if (!response.ok || !response.body) {
      onError(new Error(`HTTP ${response.status}: ${response.statusText}`))
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        // Parse SSE chunks: "event: X\ndata: {...}\n\n"
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() ?? ''

        for (const chunk of chunks) {
          const lines = chunk.trim().split('\n')
          let eventType = ''
          let dataStr = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) eventType = line.slice(7).trim()
            if (line.startsWith('data: ')) dataStr = line.slice(6).trim()
          }
          if (!eventType || !dataStr) continue
          try {
            const data = JSON.parse(dataStr)
            onEvent({ type: eventType as TurnEvent['type'], data } as TurnEvent)
          } catch {
            // ignore malformed SSE
          }
        }
      }
    } catch (e) {
      onError(e instanceof Error ? e : new Error(String(e)))
      return
    }
    onComplete()
  },
}
