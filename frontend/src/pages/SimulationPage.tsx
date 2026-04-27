import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { sessionsApi } from '../api/sessions'
import { professionsApi } from '../api/professions'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import type { DecisionResponse, SessionResponse } from '../types'
import type { ProfessionCharacter, CharacterStatus } from '../lib/professionVisuals'
import { getVisuals, statusFromScore, STATUS_CONFIG } from '../lib/professionVisuals'
import ConsequenceOverlay from '../components/session/ConsequenceOverlay'
import FeedbackDrawer from '../components/session/FeedbackDrawer'
import MetricsPanel from '../components/session/MetricsPanel'

type CharState = { status: CharacterStatus; message: string }

/* ── Action icon map ─────────────────────────────────────── */
const ACTION_ICONS: Record<string, string> = {
  listen: '👂', examine: '🔬', diagnose: '🩺', prescribe: '💊', finish: '✅',
  investigate: '🔍', negotiate: '🤝', argue: '⚖️', object: '🚫', accept: '✅',
  analyze: '📊', delegate: '👥', innovate: '💡', report: '📋', escalate: '🚨',
  code: '💻', review: '📝', deploy: '🚀', debug: '🐛', refactor: '🔧',
  ask: '❓', talk: '💬', wait: '⏳', help: '🆘', calm: '😌',
  default: '🎯',
}

function getActionIcon(key: string): string {
  const lower = key.toLowerCase()
  for (const [k, v] of Object.entries(ACTION_ICONS)) {
    if (lower.includes(k)) return v
  }
  return ACTION_ICONS.default
}

/* ── Status bubble config ────────────────────────────────── */
const STATUS_BUBBLES: Record<CharacterStatus, { emoji: string; bg: string }> = {
  stable:   { emoji: '😊', bg: 'rgba(16,185,129,0.2)' },
  worried:  { emoji: '😰', bg: 'rgba(245,158,11,0.2)' },
  active:   { emoji: '😤', bg: 'rgba(59,130,246,0.2)' },
  panic:    { emoji: '😱', bg: 'rgba(239,68,68,0.3)' },
  critical: { emoji: '🆘', bg: 'rgba(239,68,68,0.3)' },
  positive: { emoji: '😄', bg: 'rgba(16,185,129,0.2)' },
  relieved: { emoji: '😌', bg: 'rgba(16,185,129,0.2)' },
  watching: { emoji: '👀', bg: 'rgba(124,111,168,0.2)' },
  ready:    { emoji: '✅', bg: 'rgba(59,130,246,0.2)' },
  dead:     { emoji: '💀', bg: 'rgba(74,64,101,0.2)' },
}

export default function SimulationPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [session, setSession] = useState<SessionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [deciding, setDeciding] = useState(false)
  const [lastDecision, setLastDecision] = useState<DecisionResponse | null>(null)
  const [showOverlay, setShowOverlay] = useState(false)
  const [metricsBefore, setMetricsBefore] = useState<Record<string, number>>({})
  const [totalXP, setTotalXP] = useState(0)
  const [charStates, setCharStates] = useState<Record<string, CharState>>({})
  const [characters, setCharacters] = useState<ProfessionCharacter[]>([])
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [pollingFeedback, setPollingFeedback] = useState(false)
  const [activeChar, setActiveChar] = useState(0)
  const [showMetrics, setShowMetrics] = useState(false)
  const [profAccent, setProfAccent] = useState('#7c3aed')
  const [profGradient, setProfGradient] = useState('linear-gradient(135deg,#7c3aed,#e879f9)')
  const [profImage, setProfImage] = useState('')

  const stepStartTime = useRef<number>(Date.now())
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const professionId = searchParams.get('professionId')

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    if (!sessionId) return

    sessionsApi.get(sessionId)
      .then(async s => {
        if (s.status === 'completed') {
          navigate(`/session/${sessionId}/results`, { replace: true })
          return
        }
        setSession(s)
        setMetricsBefore(s.metrics)

        const pid = s.profession_id ?? professionId
        if (!pid) return
        try {
          const prof = await professionsApi.get(pid)
          const vis = getVisuals(prof)
          setCharacters(vis.characters)
          setProfAccent(vis.accent)
          setProfGradient(vis.gradient)
          setProfImage(vis.image)
          const initStates: Record<string, CharState> = {}
          vis.characters.forEach(c => { initStates[c.id] = { status: c.initStatus, message: '' } })
          setCharStates(initStates)
        } catch { /* no characters */ }
      })
      .catch(err => {
        toast(err instanceof Error ? err.message : 'Сессия табылмады', 'error')
        navigate('/professions')
      })
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, user])

  async function handleDecision(optionKey: string) {
    if (!sessionId || deciding) return
    setDeciding(true)
    const timeSpent = Math.round((Date.now() - stepStartTime.current) / 1000)

    try {
      const decision = await sessionsApi.decide(sessionId, {
        option_key: optionKey,
        time_spent_sec: Math.min(timeSpent, 3600),
      })

      setLastDecision(decision)
      setTotalXP(prev => prev + decision.xp_gained)

      const newStatus = statusFromScore(decision.step_score)
      setCharStates(prev => {
        const next = { ...prev }
        Object.keys(next).forEach(id => {
          next[id] = { status: newStatus, message: '' }
        })
        return next
      })

      setMetricsBefore(decision.metrics_before)
      if (decision.next_step) {
        setSession(prev => prev ? {
          ...prev,
          current_step: decision.next_step,
          metrics: decision.metrics_after,
          step_count: prev.step_count + 1,
        } : prev)
        stepStartTime.current = Date.now()
      }

      setShowOverlay(true)

      if (!decision.ai_feedback?.generated || !decision.ai_feedback?.text) {
        setPollingFeedback(true)
        pollForFeedback(sessionId, decision.decision_id, decision)
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Шешім қабылданбады', 'error')
    } finally {
      setDeciding(false)
    }
  }

  function pollForFeedback(sid: string, did: string, dec: DecisionResponse) {
    if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
    pollTimerRef.current = setTimeout(async () => {
      try {
        const result = await sessionsApi.getFeedback(sid, did)
        if (result.ready && result.feedback?.text) {
          setLastDecision(prev => prev ? {
            ...prev,
            ai_feedback: { ...prev.ai_feedback, ...result.feedback!, generated: true },
          } : prev)
          setPollingFeedback(false)
        } else { pollForFeedback(sid, did, dec) }
      } catch { setPollingFeedback(false) }
    }, 2000)
  }

  useEffect(() => {
    return () => { if (pollTimerRef.current) clearTimeout(pollTimerRef.current) }
  }, [])

  function handleContinue() {
    setShowOverlay(false)
    if (!lastDecision) return
    if (lastDecision.is_terminal) navigate(`/session/${sessionId}/results`)
  }

  async function handlePause() {
    if (!sessionId) return
    try {
      await sessionsApi.pause(sessionId)
      toast('Сессия кідіртілді', 'info')
      navigate('/dashboard')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Қате', 'error')
    }
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#07040f' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="w-14 h-14 rounded-full border-2 border-ogma-600 border-t-transparent animate-spin mx-auto mb-4" />
          <p style={{ color: '#7c6fa8', fontSize: 14 }}>Симуляция жүктелуде...</p>
        </div>
      </div>
    )
  }

  if (!session?.current_step) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#07040f', color: '#7c6fa8' }}>
        Сессия табылмады
      </div>
    )
  }

  const { current_step, metrics, step_count } = session
  const currentChar = characters[activeChar] ?? null
  const currentCharStatus = currentChar ? (charStates[currentChar.id]?.status ?? currentChar.initStatus) : 'watching'
  const statusCfg = STATUS_CONFIG[currentCharStatus] ?? STATUS_CONFIG.watching
  const bubble = STATUS_BUBBLES[currentCharStatus] ?? STATUS_BUBBLES.watching

  return (
    <div style={{
      minHeight: '100vh', background: '#07040f', position: 'relative', overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* ── Top HUD ── */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(180deg,rgba(7,4,15,0.95) 0%,rgba(7,4,15,0) 100%)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={handlePause}
            style={{
              width: 36, height: 36, borderRadius: 12, border: '1px solid rgba(124,58,237,0.3)',
              background: 'rgba(124,58,237,0.15)', color: '#a78bfa', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
            }}
          >
            ⏸
          </button>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#f5f0ff' }}>
              Қадам {step_count + 1}
            </div>
            <div style={{ fontSize: 10, color: '#7c6fa8' }}>{current_step.title}</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {totalXP > 0 && (
            <div style={{
              padding: '5px 12px', borderRadius: 99,
              background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)',
              fontSize: 12, fontWeight: 700, color: '#10b981',
            }}>
              +{totalXP} XP
            </div>
          )}
          <button
            onClick={() => setShowMetrics(!showMetrics)}
            style={{
              width: 36, height: 36, borderRadius: 12, border: '1px solid rgba(124,58,237,0.3)',
              background: showMetrics ? 'rgba(124,58,237,0.3)' : 'rgba(124,58,237,0.15)',
              color: '#a78bfa', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
            }}
          >
            📊
          </button>
        </div>
      </div>

      {/* ── Metrics slide-down panel ── */}
      <AnimatePresence>
        {showMetrics && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{
              position: 'fixed', top: 64, left: 0, right: 0, zIndex: 99,
              background: 'rgba(13,8,32,0.96)', backdropFilter: 'blur(20px)',
              borderBottom: '1px solid rgba(124,58,237,0.2)',
              overflow: 'hidden', padding: '0 20px',
            }}
          >
            <div style={{ padding: '16px 0', maxWidth: 600, margin: '0 auto' }}>
              <MetricsPanel metrics={metrics} metricsBefore={metricsBefore} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Character scene (upper 60%) ── */}
      <div style={{
        flex: '1 1 0', minHeight: 300, position: 'relative',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        paddingTop: 70,
      }}>
        {/* Background scene */}
        <div style={{
          position: 'absolute', inset: 0,
          background: profImage
            ? `linear-gradient(180deg,rgba(7,4,15,0.3) 0%,rgba(7,4,15,0.95) 85%),url(${profImage}) center/cover no-repeat`
            : profGradient,
          filter: 'brightness(0.35) saturate(1.3)',
        }} />

        {/* Gradient overlay bottom */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: '50%',
          background: 'linear-gradient(to top, #07040f 0%, transparent 100%)',
        }} />

        {/* Character display */}
        <div style={{ position: 'relative', zIndex: 2, width: '100%', display: 'flex', justifyContent: 'center' }}>
          {currentChar && (() => {
            const photoSrc = currentChar.statusImages?.[currentCharStatus]
            return (
              <motion.div
                key={currentChar.id + currentCharStatus}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.35 }}
                style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
              >
                {photoSrc ? (
                  /* Real NPC photo */
                  <div style={{ position: 'relative' }}>
                    <motion.img
                      key={photoSrc}
                      src={photoSrc}
                      alt={currentChar.name}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.35 }}
                      style={{
                        height: 'min(320px, 42vh)', width: 'auto', objectFit: 'contain',
                        filter: `drop-shadow(0 24px 48px ${statusCfg.color}60)`,
                      }}
                    />
                    {/* Status badge */}
                    <motion.div
                      animate={{ y: [-3, 3, -3] }}
                      transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
                      style={{
                        position: 'absolute', top: 8, right: -12,
                        padding: '6px 10px', borderRadius: 12,
                        background: bubble.bg, backdropFilter: 'blur(8px)',
                        border: `1px solid ${statusCfg.color}50`,
                        display: 'flex', alignItems: 'center', gap: 5,
                      }}
                    >
                      <span style={{ fontSize: 16 }}>{bubble.emoji}</span>
                      <span style={{ fontSize: 10, color: statusCfg.color, fontWeight: 700 }}>
                        {statusCfg.label}
                      </span>
                    </motion.div>
                  </div>
                ) : (
                  /* Fallback emoji avatar */
                  <div style={{ position: 'relative' }}>
                    <div style={{
                      width: 160, height: 160, borderRadius: 40,
                      background: `linear-gradient(135deg,${profAccent}30,rgba(124,58,237,0.2))`,
                      border: `3px solid ${statusCfg.color}60`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 80, boxShadow: `0 20px 60px ${profAccent}30, 0 0 40px ${statusCfg.color}20`,
                      margin: '0 auto',
                    }}>
                      {currentChar.avatar}
                    </div>
                    <motion.div
                      animate={{ y: [-3, 3, -3] }}
                      transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
                      style={{
                        position: 'absolute', top: -16, right: -20,
                        padding: '6px 10px', borderRadius: 12,
                        background: bubble.bg, backdropFilter: 'blur(8px)',
                        border: `1px solid ${statusCfg.color}50`,
                        display: 'flex', alignItems: 'center', gap: 5,
                      }}
                    >
                      <span style={{ fontSize: 16 }}>{bubble.emoji}</span>
                      <span style={{ fontSize: 10, color: statusCfg.color, fontWeight: 700 }}>
                        {statusCfg.label}
                      </span>
                    </motion.div>
                  </div>
                )}

                {/* Name & role tag */}
                <div style={{
                  marginTop: 10, padding: '5px 16px', borderRadius: 99,
                  background: 'rgba(13,8,32,0.75)', backdropFilter: 'blur(8px)',
                  border: `1px solid ${statusCfg.color}30`,
                  display: 'flex', alignItems: 'center', gap: 8,
                }}>
                  <span style={{ fontSize: 14, fontWeight: 800, color: '#f5f0ff' }}>{currentChar.name}</span>
                  <span style={{ fontSize: 11, color: '#7c6fa8' }}>{currentChar.role}</span>
                </div>
              </motion.div>
            )
          })()}

          {/* Character switcher dots */}
          {characters.length > 1 && (
            <div style={{ position: 'absolute', bottom: -8, left: 0, right: 0, display: 'flex', gap: 8, justifyContent: 'center' }}>
              {characters.map((c, i) => {
                const st = charStates[c.id]?.status ?? c.initStatus
                const col = STATUS_CONFIG[st]?.color ?? '#7c6fa8'
                return (
                  <button
                    key={c.id}
                    onClick={() => setActiveChar(i)}
                    style={{
                      width: activeChar === i ? 40 : 10, height: 10, borderRadius: 99,
                      background: activeChar === i ? col : `${col}40`,
                      border: 'none', cursor: 'pointer',
                      transition: 'all 0.3s ease',
                    }}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── Narrative text ── */}
      <div style={{
        padding: '0 20px 12px', position: 'relative', zIndex: 2,
      }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={current_step.step_key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            style={{
              padding: '16px 20px', borderRadius: 20,
              background: 'rgba(20,15,46,0.85)', backdropFilter: 'blur(12px)',
              border: '1px solid rgba(124,58,237,0.2)',
            }}
          >
            <p style={{
              fontSize: 14, lineHeight: 1.7, color: '#c4b5fd', margin: 0,
            }}>
              {current_step.narrative}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ── Action buttons (game-style bottom bar) ── */}
      <div style={{
        padding: '8px 12px 24px', position: 'relative', zIndex: 2,
        background: 'linear-gradient(to top, rgba(7,4,15,1) 60%, transparent 100%)',
      }}>
        <p style={{
          fontSize: 10, fontWeight: 700, color: '#7c6fa8',
          textTransform: 'uppercase', letterSpacing: '0.1em',
          textAlign: 'center', margin: '0 0 10px',
        }}>
          Шешім қабылдаңыз
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.min(current_step.available_options.length, 5)}, 1fr)`,
          gap: 8,
        }}>
          {current_step.available_options.map((opt, i) => {
            const isDisabled = deciding || showOverlay || !opt.is_available
            const icon = getActionIcon(opt.option_key)

            return (
              <motion.button
                key={opt.option_key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                whileHover={!isDisabled ? { y: -4, scale: 1.04 } : {}}
                whileTap={!isDisabled ? { scale: 0.95 } : {}}
                onClick={() => !isDisabled && handleDecision(opt.option_key)}
                disabled={isDisabled}
                style={{
                  padding: '12px 6px', borderRadius: 16,
                  background: isDisabled
                    ? 'rgba(20,15,46,0.4)'
                    : `linear-gradient(180deg,${profAccent}25,rgba(20,15,46,0.8))`,
                  border: `1.5px solid ${isDisabled ? 'rgba(74,64,101,0.3)' : profAccent + '50'}`,
                  cursor: isDisabled ? 'not-allowed' : 'pointer',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                  transition: 'all 0.2s',
                  opacity: isDisabled ? 0.4 : 1,
                  boxShadow: isDisabled ? 'none' : `0 4px 20px ${profAccent}15`,
                }}
              >
                <span style={{
                  fontSize: 28, display: 'block', lineHeight: 1,
                  filter: isDisabled ? 'grayscale(1)' : 'none',
                }}>
                  {icon}
                </span>
                <span style={{
                  fontSize: 9, fontWeight: 700, color: isDisabled ? '#4a4065' : '#c4b5fd',
                  textTransform: 'uppercase', letterSpacing: '0.02em',
                  lineHeight: 1.3, textAlign: 'center',
                  display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}>
                  {opt.label}
                </span>
              </motion.button>
            )
          })}
        </div>
      </div>

      {/* ── Consequence Overlay ── */}
      {showOverlay && lastDecision && (
        <ConsequenceOverlay
          decision={lastDecision}
          characters={characters.map(c => ({ ...c, status: charStates[c.id]?.status ?? c.initStatus }))}
          onContinue={handleContinue}
          onShowFeedback={() => { setShowOverlay(false); setFeedbackOpen(true) }}
          feedbackLoading={pollingFeedback}
        />
      )}

      {/* ── AI Feedback Drawer ── */}
      <FeedbackDrawer
        open={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        decision={lastDecision}
      />
    </div>
  )
}
