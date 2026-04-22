import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { sessionsApi } from '../api/sessions'
import { professionsApi } from '../api/professions'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import type { DecisionResponse, SessionResponse } from '../types'
import type { ProfessionCharacter, CharacterStatus } from '../lib/professionVisuals'
import { getVisuals, statusFromScore } from '../lib/professionVisuals'
import StepDisplay from '../components/session/StepDisplay'
import OptionCard from '../components/session/OptionCard'
import MetricsPanel from '../components/session/MetricsPanel'
import CharacterCard from '../components/session/CharacterCard'
import ConsequenceOverlay from '../components/session/ConsequenceOverlay'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'

type CharState = { status: CharacterStatus; message: string }

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

  const stepStartTime = useRef<number>(Date.now())

  // professionId may be passed as query param when navigating from scenarios
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

        // Load profession visuals if professionId is available
        const pid = professionId ?? s.scenario_id  // fallback: use scenario_id as slug hint
        try {
          const prof = await professionsApi.get(pid)
          const vis = getVisuals(prof)
          setCharacters(vis.characters)
          const initStates: Record<string, CharState> = {}
          vis.characters.forEach(c => { initStates[c.id] = { status: c.initStatus, message: '' } })
          setCharStates(initStates)
        } catch {
          // profession not found — no characters, that's OK
        }
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

      // Update character states based on decision score
      const newStatus = statusFromScore(decision.step_score)
      setCharStates(prev => {
        const next = { ...prev }
        Object.keys(next).forEach(id => {
          next[id] = { status: newStatus, message: '' }
        })
        return next
      })

      // Update session metrics
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
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Шешім қабылданбады', 'error')
    } finally {
      setDeciding(false)
    }
  }

  function handleContinue() {
    setShowOverlay(false)
    if (!lastDecision) return
    if (lastDecision.is_terminal) {
      navigate(`/session/${sessionId}/results`)
    }
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-ogma-600 border-t-transparent animate-spin" />
          <p className="text-ogma-muted text-sm">Сессия жүктелуде...</p>
        </div>
      </div>
    )
  }

  if (!session?.current_step) {
    return (
      <div className="min-h-screen flex items-center justify-center text-ogma-muted">
        Сессия табылмады
      </div>
    )
  }

  const { current_step, metrics, step_count, status } = session

  // Determine accent colour from visuals (if characters loaded)
  const accentColor = '#7c3aed'
  const gradient = 'linear-gradient(135deg,#7c3aed,#e879f9)'

  return (
    <div style={{ minHeight: '100vh', paddingTop: 80, paddingBottom: 64, background: '#07040f', position: 'relative' }}>
      <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none opacity-40" />
      <div className="orb w-80 h-80 bg-ogma-600 opacity-[0.07] top-[-60px] right-[-60px]" />

      <div className="page-container relative z-10">
        {/* ── Top bar ── */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
          <div className="flex items-center gap-3">
            <Badge variant={status === 'active' ? 'success' : 'warning'} dot>
              {status === 'active' ? 'Белсенді' : 'Кідіртілген'}
            </Badge>
            <span className="text-sm text-ogma-muted">Қадам {step_count + 1}</span>
            {totalXP > 0 && (
              <span
                className="text-sm font-semibold"
                style={{ color: accentColor }}
              >
                +{totalXP} XP
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handlePause}>
              Кідірту
            </Button>
          </div>
        </motion.div>

        {/* ── Character cards ── */}
        {characters.length > 0 && (
          <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
            {characters.map(c => (
              <CharacterCard
                key={c.id}
                char={{ ...c, status: charStates[c.id]?.status ?? c.initStatus }}
                message={charStates[c.id]?.message || undefined}
              />
            ))}
          </div>
        )}

        {/* ── Main grid ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: 20 }}>

          {/* Left: narrative + options */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <AnimatePresence mode="wait">
              <StepDisplay
                key={current_step.step_key}
                step={current_step}
                stepNumber={step_count + 1}
              />
            </AnimatePresence>

            <div className="bento">
              <h3
                className="text-xs font-bold text-ogma-secondary mb-4 uppercase tracking-wider flex items-center gap-2"
              >
                <span
                  style={{ width: 3, height: 14, borderRadius: 99, background: gradient, display: 'inline-block' }}
                />
                Шешім қабылдаңыз
              </h3>
              <div className="flex flex-col gap-3">
                {current_step.available_options.map((opt, i) => (
                  <OptionCard
                    key={opt.option_key}
                    option={opt}
                    index={i}
                    selected={lastDecision?.option_key === opt.option_key && !showOverlay}
                    disabled={deciding || showOverlay}
                    onSelect={handleDecision}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Right: metrics + XP + progress */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <MetricsPanel metrics={metrics} metricsBefore={metricsBefore} />

            {/* XP counter */}
            <div className="bento text-center">
              <p style={{ fontSize: 10, color: '#7c6fa8', margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Жинақталған XP
              </p>
              <p
                style={{
                  fontSize: 32, fontWeight: 900, margin: '0 0 4px',
                  background: gradient, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                }}
              >
                +{totalXP}
              </p>
              <div style={{ height: 3, background: 'rgba(124,58,237,0.12)', borderRadius: 99, overflow: 'hidden', marginTop: 8 }}>
                <div
                  style={{
                    height: '100%',
                    width: `${Math.min(100, (totalXP / 200) * 100)}%`,
                    background: gradient, borderRadius: 99,
                    transition: 'width 0.6s ease',
                  }}
                />
              </div>
            </div>

            {/* Step count badge */}
            <div className="bento text-center">
              <p style={{ fontSize: 10, color: '#7c6fa8', margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Шешімдер
              </p>
              <p style={{ fontSize: 28, fontWeight: 900, color: '#f5f0ff', margin: 0 }}>{step_count}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Consequence Overlay ── */}
      {showOverlay && lastDecision && (
        <ConsequenceOverlay
          decision={lastDecision}
          characters={characters.map(c => ({ ...c, status: charStates[c.id]?.status ?? c.initStatus }))}
          onContinue={handleContinue}
        />
      )}
    </div>
  )
}
