/**
 * useOpenWorldSession — single source of truth for an open-world session.
 *
 * State slices updated progressively as SSE events arrive:
 *   intent → validation → npc → world → scene → [terminal] → done
 *
 * The `sendTurn(text)` function kicks off a new turn.
 * While streaming, `isStreaming` is true and the input is locked.
 */
import { useCallback, useRef, useState } from 'react'
import {
  openWorldApi,
  type DoneEvent,
  type IntentEvent,
  type NpcEvent,
  type OpenWorldSession,
  type SceneEvent,
  type TerminalEvent,
  type TurnEvent,
  type ValidationEvent,
  type WorldEvent,
} from '../api/openWorld'

export interface TurnSnapshot {
  turnIndex: number
  userInput: string
  intent: IntentEvent | null
  validation: ValidationEvent | null
  npc: NpcEvent | null
  world: WorldEvent | null
  scene: SceneEvent | null
  terminal: TerminalEvent | null
}

export interface OpenWorldState {
  session: OpenWorldSession | null
  // Current world metrics (updated on each 'world' event)
  currentMetrics: Record<string, number>
  // NPC running state
  npcEmotion: Record<string, number>
  npcLabel: string
  npcUtterance: string
  npcBodyLanguage: string
  npcAvatarId: string
  // Current scene image
  sceneImageUrl: string
  sceneAltText: string
  sceneIsFallback: boolean
  // Turn tracking
  turnIndex: number
  isStreaming: boolean
  isTerminal: boolean
  terminalEvent: TerminalEvent | null
  // Latest partial turn (shown in TurnResultStrip)
  latestTurn: TurnSnapshot | null
  // History
  turns: TurnSnapshot[]
  // Suggested action chips
  suggestedActions: string[]
  // Error message (if any)
  error: string | null
}

const initialState: OpenWorldState = {
  session: null,
  currentMetrics: {},
  npcEmotion: {},
  npcLabel: '',
  npcUtterance: '',
  npcBodyLanguage: '',
  npcAvatarId: '',
  sceneImageUrl: '',
  sceneAltText: '',
  sceneIsFallback: false,
  turnIndex: 0,
  isStreaming: false,
  isTerminal: false,
  terminalEvent: null,
  latestTurn: null,
  turns: [],
  suggestedActions: [],
  error: null,
}

export function useOpenWorldSession() {
  const [state, setState] = useState<OpenWorldState>(initialState)
  const inProgressTurn = useRef<TurnSnapshot | null>(null)

  const loadSession = useCallback((session: OpenWorldSession) => {
    setState(prev => ({
      ...prev,
      session,
      currentMetrics: session.initial_world_state.metrics,
      npcEmotion: session.npc.initial_emotion,
      npcLabel: '',
      npcUtterance: '',
      npcBodyLanguage: '',
      npcAvatarId: session.npc.avatar_image_id || '',
      sceneImageUrl: '',
      sceneAltText: '',
      sceneIsFallback: false,
      turnIndex: 0,
      isTerminal: false,
      terminalEvent: null,
      latestTurn: null,
      turns: [],
      suggestedActions: session.initial_suggested_actions,
      error: null,
    }))
  }, [])

  const sendTurn = useCallback(async (userText: string, locale = 'kk') => {
    const sessionId = state.session?.session_id
    if (!sessionId || state.isStreaming || !userText.trim()) return

    // Init the in-progress turn snapshot
    inProgressTurn.current = {
      turnIndex: state.turnIndex,
      userInput: userText,
      intent: null,
      validation: null,
      npc: null,
      world: null,
      scene: null,
      terminal: null,
    }

    setState(prev => ({
      ...prev,
      isStreaming: true,
      error: null,
      latestTurn: inProgressTurn.current,
    }))

    const handleEvent = (event: TurnEvent) => {
      const current = inProgressTurn.current
      if (!current) return

      setState(prev => {
        const updated = { ...prev }

        switch (event.type) {
          case 'intent':
            inProgressTurn.current = { ...current, intent: event.data }
            updated.latestTurn = inProgressTurn.current
            break

          case 'validation':
            inProgressTurn.current = { ...current, validation: event.data }
            updated.latestTurn = inProgressTurn.current
            break

          case 'npc': {
            // Apply emotion delta
            const newEmotion = { ...prev.npcEmotion }
            for (const [k, v] of Object.entries(event.data.emotion_delta)) {
              newEmotion[k] = Math.max(0, Math.min(100, (newEmotion[k] ?? 50) + v))
            }
            inProgressTurn.current = { ...current, npc: event.data }
            updated.npcEmotion = newEmotion
            updated.npcLabel = event.data.new_state_label
            updated.npcUtterance = event.data.utterance
            updated.npcBodyLanguage = event.data.body_language
            if (event.data.suggested_avatar_id) {
              updated.npcAvatarId = event.data.suggested_avatar_id
            }
            updated.latestTurn = inProgressTurn.current
            break
          }

          case 'world':
            inProgressTurn.current = { ...current, world: event.data }
            updated.currentMetrics = event.data.current_metrics
            updated.latestTurn = inProgressTurn.current
            break

          case 'scene':
            inProgressTurn.current = { ...current, scene: event.data }
            updated.sceneImageUrl = event.data.image_url
            updated.sceneAltText = event.data.alt_text
            updated.sceneIsFallback = event.data.is_fallback
            updated.latestTurn = inProgressTurn.current
            break

          case 'terminal':
            inProgressTurn.current = { ...current, terminal: event.data }
            updated.isTerminal = true
            updated.terminalEvent = event.data
            updated.latestTurn = inProgressTurn.current
            break

          case 'done': {
            const completedTurn = inProgressTurn.current!
            updated.turns = [...prev.turns, completedTurn]
            updated.turnIndex = (event.data as DoneEvent).turn_index + 1
            updated.isStreaming = false
            inProgressTurn.current = null
            break
          }

          case 'error':
            updated.error = event.data.message
            updated.isStreaming = false
            inProgressTurn.current = null
            break
        }

        return updated
      })
    }

    const handleComplete = () => {
      setState(prev => ({ ...prev, isStreaming: false }))
      // Refresh suggested actions
      openWorldApi.getSuggestedActions(sessionId).then(actions => {
        setState(prev => ({ ...prev, suggestedActions: actions }))
      }).catch(() => {/* ignore */})
    }

    const handleError = (err: Error) => {
      setState(prev => ({ ...prev, isStreaming: false, error: err.message }))
    }

    await openWorldApi.streamTurn(sessionId, userText, locale, handleEvent, handleComplete, handleError)
  }, [state.session, state.isStreaming, state.turnIndex])

  return { state, loadSession, sendTurn }
}
