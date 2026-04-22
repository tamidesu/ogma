import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { sessionsApi } from '../api/sessions'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import type { DecisionHistoryItem, SessionResponse } from '../types'
import MetricsPanel from '../components/session/MetricsPanel'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Particles from '../components/common/Particles'

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.45 }}
    >
      {children}
    </motion.div>
  )
}

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [session, setSession] = useState<SessionResponse | null>(null)
  const [history, setHistory] = useState<DecisionHistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    if (!sessionId) return
    Promise.all([
      sessionsApi.get(sessionId),
      sessionsApi.history(sessionId),
    ])
      .then(([s, h]) => { setSession(s); setHistory(h) })
      .catch(err => {
        toast(err instanceof Error ? err.message : 'Нәтиже жүктелмеді', 'error')
        navigate('/dashboard')
      })
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, user])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-ogma-600 border-t-transparent animate-spin" />
          <p className="text-ogma-muted text-sm">Нәтижелер жүктелуде...</p>
        </div>
      </div>
    )
  }

  if (!session) return null

  const finalScore = session.final_score ?? 0
  const scoreGrade = finalScore >= 80 ? 'Тамаша' : finalScore >= 60 ? 'Жақсы' : 'Жақсартуды қажет ете'
  const scoreVariant: 'success' | 'info' | 'warning' =
    finalScore >= 80 ? 'success' : finalScore >= 60 ? 'info' : 'warning'
  return (
    <div
      style={{ minHeight: '100vh', paddingTop: 80, paddingBottom: 64, background: '#07040f', position: 'relative', overflow: 'hidden' }}
    >
      <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none opacity-30" />
      <div className="orb w-[500px] h-[500px] bg-ogma-600 opacity-10 top-[-100px]"
        style={{ left: '50%', transform: 'translateX(-50%)' }}
      />
      <Particles color="#7c3aed" count={18} />

      <div className="page-container relative z-10">

        {/* ── Score hero ── */}
        <FadeIn>
          <div style={{ textAlign: 'center', marginBottom: 52 }}>
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', damping: 14, stiffness: 180, delay: 0.1 }}
              style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 14, marginBottom: 18 }}
            >
              <div style={{ position: 'relative' }}>
                <div style={{
                  width: 144, height: 144, borderRadius: '50%',
                  background: 'linear-gradient(135deg,#7c3aed,#e879f9)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: '0 0 60px rgba(124,58,237,0.5)',
                }}>
                  <span style={{ fontSize: 44, fontWeight: 900, color: '#fff' }}>
                    {Math.round(finalScore)}
                  </span>
                </div>
                <div style={{
                  position: 'absolute', inset: 0, borderRadius: '50%',
                  background: 'linear-gradient(135deg,#7c3aed,#e879f9)',
                  opacity: 0.2, filter: 'blur(20px)',
                  animation: 'glowPulse 3s ease-in-out infinite',
                }} />
              </div>
              <Badge variant={scoreVariant} size="md">{scoreGrade}</Badge>
            </motion.div>

            <h1 style={{ fontSize: 'clamp(26px,4vw,38px)', fontWeight: 900, color: '#f5f0ff', margin: '0 0 6px' }}>
              Сессия аяқталды!
            </h1>
            <p style={{ color: '#7c6fa8', margin: 0 }}>
              {session.step_count} шешім қабылдадыңыз
            </p>
          </div>
        </FadeIn>

        {/* ── Grid: Metrics + History ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 22, marginBottom: 36 }}>
          <FadeIn delay={0.1}>
            <MetricsPanel metrics={session.metrics} />
          </FadeIn>

          <FadeIn delay={0.15}>
            <div className="bento" style={{ height: '100%' }}>
              <h3 className="text-sm font-semibold text-ogma-secondary mb-4 flex items-center gap-2">
                <span style={{ width: 3, height: 16, borderRadius: 99, background: 'linear-gradient(#e879f9,#7c3aed)', display: 'inline-block' }} />
                Шешімдер тарихы ({history.length})
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 400, overflowY: 'auto', paddingRight: 4 }}>
                {history.map((item, i) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    style={{
                      padding: '13px 15px', borderRadius: 13,
                      background: 'rgba(28,22,64,0.5)',
                      border: '1px solid rgba(124,58,237,0.15)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#a78bfa' }}>#{i + 1}</span>
                      <span style={{ fontSize: 11, color: '#7c6fa8', fontFamily: 'monospace' }}>{item.step_key}</span>
                      {item.time_spent_sec != null && (
                        <span style={{ fontSize: 10, color: '#4a4065', marginLeft: 'auto' }}>
                          {item.time_spent_sec}с
                        </span>
                      )}
                    </div>

                    <p style={{ fontSize: 13, color: '#c4b5fd', fontWeight: 600, margin: '0 0 5px' }}>
                      {item.option_key}
                    </p>

                    {/* Metric deltas */}
                    {Object.keys(item.metrics_after ?? {}).length > 0 && (
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                        {Object.entries(item.metrics_after ?? {}).map(([key, val]) => {
                          const before = (item.metrics_before ?? {})[key] ?? val
                          const d = (val as number) - (before as number)
                          if (Math.abs(d) < 1) return null
                          return (
                            <span
                              key={key}
                              style={{
                                fontSize: 10, fontWeight: 700,
                                color: d > 0 ? '#10b981' : '#ef4444',
                                background: d > 0 ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                                padding: '1px 7px', borderRadius: 99,
                                border: `1px solid ${d > 0 ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                              }}
                            >
                              {key} {d > 0 ? '+' : ''}{Math.round(d)}
                            </span>
                          )
                        })}
                      </div>
                    )}

                    {item.ai_feedback?.key_insight && (
                      <p style={{ fontSize: 11, color: '#7c6fa8', lineHeight: 1.5, margin: 0 }}>
                        💡 {item.ai_feedback.key_insight}
                      </p>
                    )}
                  </motion.div>
                ))}

                {history.length === 0 && (
                  <p style={{ fontSize: 13, color: '#7c6fa8', textAlign: 'center', padding: '24px 0' }}>
                    Шешімдер тарихы жоқ
                  </p>
                )}
              </div>
            </div>
          </FadeIn>
        </div>

        {/* ── Actions ── */}
        <FadeIn delay={0.2}>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button size="lg" onClick={() => navigate('/professions')}>
              Жаңа сценарий бастау →
            </Button>
            <Button size="lg" variant="ghost" onClick={() => navigate('/dashboard')}>
              Панельге оралу
            </Button>
          </div>
        </FadeIn>
      </div>

      {/* Score ring accent */}
      <style>{`
        @keyframes glowPulse {
          0%,100% { opacity: 0.2; }
          50%      { opacity: 0.45; }
        }
      `}</style>
    </div>
  )
}
