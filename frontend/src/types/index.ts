// ── Envelope ────────────────────────────────────────────────────────────────
export interface ResponseEnvelope<T> {
  data: T | null
  meta: Record<string, unknown>
  errors: { code: string; message: string } | null
}

// ── Auth ─────────────────────────────────────────────────────────────────────
export interface UserResponse {
  id: string
  email: string
  display_name: string | null
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RefreshRequest {
  refresh_token: string
}

// ── Professions ───────────────────────────────────────────────────────────────
export interface ProfessionResponse {
  id: string
  slug: string
  name: string
  description: string | null
  icon_key: string | null
  color_hex: string | null
  difficulty_label: string | null
}

export interface ScenarioSummaryResponse {
  id: string
  slug: string
  title: string
  description: string
  difficulty: number
  estimated_steps: number
  tags: string[]
}

// ── Sessions ──────────────────────────────────────────────────────────────────
export interface OptionInfo {
  option_key: string
  label: string
  description: string | null
  is_available: boolean
}

export interface StepInfo {
  step_key: string
  title: string
  narrative: string
  step_type: string
  available_options: OptionInfo[]
}

export interface SessionResponse {
  session_id: string
  status: 'active' | 'paused' | 'completed' | 'abandoned'
  scenario_id: string
  current_step: StepInfo | null
  metrics: Record<string, number>
  step_count: number
  started_at: string
  /** Populated only on completed sessions */
  final_score: number | null
}

export interface SkillEarned {
  skill: string
  xp_gained: number
}

export interface AIFeedbackResponse {
  text: string | null
  generated: boolean
  tone: 'encouraging' | 'critical' | 'neutral' | null
  key_insight: string | null
  coaching_question: string | null
  consequence_analysis: string | null
  alternative_path: string | null
}

export interface DecisionResponse {
  decision_id: string
  option_key: string
  effects_applied: Record<string, unknown>[]
  metrics_before: Record<string, number>
  metrics_after: Record<string, number>
  step_score: number
  next_step: StepInfo | null
  is_terminal: boolean
  final_score: number | null
  skills_earned: SkillEarned[]
  xp_gained: number
  leveled_up: boolean
  ai_feedback: AIFeedbackResponse
}

export interface DecisionHistoryItem {
  id: string
  step_key: string
  option_key: string
  metrics_before: Record<string, number>
  metrics_after: Record<string, number>
  effects_applied: Record<string, unknown>[]
  decided_at: string
  time_spent_sec: number | null
  ai_feedback: AIFeedbackResponse | null
}

export interface FeedbackPollResponse {
  decision_id: string
  ready: boolean
  feedback: AIFeedbackResponse | null
}

export interface CreateSessionRequest {
  scenario_id: string
}

export interface MakeDecisionRequest {
  option_key: string
  time_spent_sec?: number
}

// ── Progress ──────────────────────────────────────────────────────────────────
export interface SkillScoreItem {
  profession_id: string
  skill_key: string
  score: number
}

export interface ProgressResponse {
  level: number
  xp_total: number
  xp_to_next_level: number
  skill_scores: SkillScoreItem[]
  scenarios_completed: number
}

export interface SessionSummaryResponse {
  session_id: string
  scenario_id: string
  status: string
  final_score: number | null
  started_at: string
  completed_at: string | null
}
