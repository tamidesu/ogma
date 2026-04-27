/**
 * OpenWorldPage — the new open-world simulation experience.
 *
 * Layout (desktop):
 *   ┌──────────────────────────────────────────────────────────┐
 *   │  Top bar: title · turn counter · elapsed time           │
 *   ├──────────────────────────────────────────────────────────┤
 *   │  NPC Panel  │   <SceneStage>  (full-bleed image)   │ Metrics │
 *   ├──────────────────────────────────────────────────────────┤
 *   │  TurnResultStrip (collapsible)                          │
 *   ├──────────────────────────────────────────────────────────┤
 *   │  ActionInput (free-text + chips)                        │
 *   └──────────────────────────────────────────────────────────┘
 *
 * Route: /open-world/:briefId — starts a new session from a brief.
 * Route: /open-world/session/:sessionId — resumes an existing session.
 */
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { brifsApi, openWorldApi, type BriefDetail } from '../api/openWorld'
import CaseFile from '../components/openworld/CaseFile'
import NPCPanel from '../components/openworld/NPCPanel'
import SceneStage from '../components/openworld/SceneStage'
import TurnResultStrip from '../components/openworld/TurnResultStrip'
import WorldMetrics from '../components/openworld/WorldMetrics'
import ActionInput from '../components/openworld/ActionInput'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { useOpenWorldSession } from '../hooks/useOpenWorldSession'

export default function OpenWorldPage() {
  const { briefId, sessionId: existingSessionId } = useParams<{
    briefId?: string
    sessionId?: string
  }>()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const { state, loadSession, sendTurn } = useOpenWorldSession()

  const [brief, setBrief] = useState<BriefDetail | null>(null)
  const [showCaseFile, setShowCaseFile] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { navigate('/login'); return }

    async function boot() {
      try {
        if (briefId) {
          // New session from a brief
          const briefData = await brifsApi.get(briefId)
          setBrief(briefData)
          const session = await openWorldApi.createSession(briefId)
          loadSession(session)
          setShowCaseFile(true)
        } else if (existingSessionId) {
          // Resume existing session
          const stateData = await openWorldApi.getState(existingSessionId)
          // We need to load the brief separately for the metadata
          // For now, just load the session state
          toast('Сессия жалғастырылуда', 'info')
        }
      } catch (err) {
        toast(err instanceof Error ? err.message : 'Жүктеу қатесі', 'error')
        navigate('/professions')
      } finally {
        setLoading(false)
      }
    }
    boot()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [briefId, existingSessionId, user])

  function handleSendTurn(text: string) {
    sendTurn(text, brief?.locale ?? 'kk')
  }

  // Determine if world state is dire (desaturate scene)
  const isDire = (state.currentMetrics.patient_stability ?? 100) < 30
    || (state.currentMetrics.team_trust ?? 100) < 20

  // Latest delta for metric bars
  const latestDelta = state.latestTurn?.world?.metric_delta ?? {}

  const phase = state.session
    ? (state.session.initial_world_state.time?.current_phase ?? '')
    : ''

  if (loading) {
    return (
      <div className="min-h-screen bg-ogma-bg flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 rounded-full border-2 border-ogma-600 border-t-transparent
                          animate-spin mx-auto" />
          <p className="text-ogma-muted text-sm">Сценарий жүктелуде...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-ogma-bg flex flex-col">
      {/* Case file modal */}
      <AnimatePresence>
        {showCaseFile && brief && state.session && (
          <CaseFile
            brief={brief}
            onBegin={() => setShowCaseFile(false)}
          />
        )}
      </AnimatePresence>

      {/* Top bar */}
      <div className="border-b border-ogma-stroke bg-ogma-surface/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-12 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-ogma-600 font-bold text-sm tracking-wide">OGMA</span>
            {brief && (
              <>
                <span className="text-ogma-stroke">·</span>
                <span className="text-ogma-text text-sm font-medium truncate max-w-xs">
                  {brief.title}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-4 text-xs text-ogma-muted">
            {state.session && (
              <>
                <span>
                  Бетбұрыс {state.turnIndex}/{state.session.max_turns}
                </span>
                <span>
                  ⏱ {state.latestTurn?.world?.elapsed_min ?? 0} мин
                </span>
              </>
            )}
            {state.isTerminal && (
              <span className={`font-semibold ${
                state.terminalEvent?.termination_reason === 'success'
                  ? 'text-ogma-success' : 'text-ogma-error'
              }`}>
                {state.terminalEvent?.termination_reason === 'success' ? '✓ Сәтті' : '✗ Аяқталды'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 py-4">
        <div className="grid grid-cols-[240px_1fr_220px] gap-4 h-[calc(100vh-11rem)]">

          {/* Left: NPC Panel */}
          <div className="flex flex-col gap-4">
            <div className="flex-1">
              {state.session && (
                <NPCPanel
                  displayName={state.session.npc.display_name}
                  role={state.session.npc.role}
                  avatarImageId={state.npcAvatarId}
                  emotion={state.npcEmotion}
                  stateLabel={state.npcLabel}
                  utterance={state.npcUtterance}
                  bodyLanguage={state.npcBodyLanguage}
                  isStreaming={state.isStreaming}
                />
              )}
            </div>
          </div>

          {/* Center: Scene stage */}
          <div className="relative">
            <SceneStage
              imageUrl={state.sceneImageUrl}
              altText={state.sceneAltText}
              isLoading={state.isStreaming && !state.sceneImageUrl}
              desaturate={isDire}
            />

            {/* NPC quote overlay */}
            <AnimatePresence>
              {state.npcUtterance && (
                <motion.div
                  key={state.npcUtterance}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                  className="absolute bottom-4 left-4 right-4 z-10"
                >
                  <div className="bg-ogma-bg/80 backdrop-blur-sm border border-ogma-stroke
                                  rounded-xl px-4 py-3 max-w-xl">
                    <p className="text-ogma-text text-sm leading-relaxed">
                      „{state.npcUtterance}"
                    </p>
                    {state.npcBodyLanguage && (
                      <p className="text-ogma-muted text-xs italic mt-1">
                        {state.npcBodyLanguage}
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right: Metrics */}
          <div className="flex flex-col gap-4">
            <WorldMetrics
              metrics={state.currentMetrics}
              delta={latestDelta}
              elapsedMin={state.latestTurn?.world?.elapsed_min}
              phase={phase}
              turnIndex={state.turnIndex}
              maxTurns={state.session?.max_turns}
            />

            {/* XP gained this turn */}
            <AnimatePresence>
              {state.latestTurn?.world?.skill_xp && state.latestTurn.world.skill_xp.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0 }}
                  className="p-3 rounded-xl bg-ogma-surface border border-ogma-stroke"
                >
                  <p className="text-xs text-ogma-muted mb-2 uppercase tracking-wider">XP</p>
                  <div className="space-y-1">
                    {state.latestTurn.world.skill_xp.map(({ skill, xp }) => (
                      <div key={skill} className="flex justify-between text-xs">
                        <span className="text-ogma-secondary">
                          {skill.replace(/_/g, ' ')}
                        </span>
                        <span className="text-ogma-success font-semibold">+{xp}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Bottom panel */}
        <div className="mt-4 space-y-3">
          {/* Turn result strip */}
          <TurnResultStrip
            turn={state.latestTurn}
            isStreaming={state.isStreaming}
          />

          {/* Terminal message */}
          <AnimatePresence>
            {state.isTerminal && state.terminalEvent && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 rounded-xl border text-sm ${
                  state.terminalEvent.termination_reason === 'success'
                    ? 'bg-ogma-success/10 border-ogma-success/30 text-ogma-success'
                    : state.terminalEvent.termination_reason === 'failure'
                    ? 'bg-ogma-error/10 border-ogma-error/30 text-ogma-error'
                    : 'bg-ogma-warning/10 border-ogma-warning/30 text-ogma-warning'
                }`}
              >
                <p className="font-semibold mb-1">
                  {state.terminalEvent.termination_reason === 'success'
                    ? '✅ Сценарий сәтті аяқталды!'
                    : state.terminalEvent.termination_reason === 'failure'
                    ? '❌ Сценарий сәтсіз аяқталды.'
                    : '⏰ Уақыт бітті.'}
                </p>
                {state.terminalEvent.timeout_resolution && (
                  <p className="text-sm opacity-80">{state.terminalEvent.timeout_resolution}</p>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action input */}
          <ActionInput
            onSubmit={handleSendTurn}
            suggestedActions={state.suggestedActions}
            isStreaming={state.isStreaming}
            isTerminal={state.isTerminal}
            locale={brief?.locale ?? 'kk'}
          />
        </div>
      </div>

      {/* Error toast */}
      <AnimatePresence>
        {state.error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50
                       px-5 py-3 rounded-xl bg-ogma-error/20 border border-ogma-error/40
                       text-ogma-error text-sm shadow-card-lg"
          >
            {state.error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
