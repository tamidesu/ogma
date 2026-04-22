import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { professionsApi } from '../api/professions'
import { sessionsApi } from '../api/sessions'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import type { ProfessionResponse, ScenarioSummaryResponse } from '../types'
import { getVisuals } from '../lib/professionVisuals'
import Particles from '../components/common/Particles'
import Button from '../components/ui/Button'

export default function ScenariosPage() {
  const { professionId } = useParams<{ professionId: string }>()
  const { user } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [profession, setProfession] = useState<ProfessionResponse | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioSummaryResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [startingId, setStartingId] = useState<string | null>(null)
  const [imgOk, setImgOk] = useState(true)

  useEffect(() => {
    if (!professionId) return
    Promise.all([
      professionsApi.get(professionId),
      professionsApi.scenarios(professionId),
    ])
      .then(([p, s]) => { setProfession(p); setScenarios(s) })
      .catch(err => toast(err instanceof Error ? err.message : 'Қате орын алды', 'error'))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [professionId])

  async function handleStart(scenarioId: string) {
    if (!user) { navigate('/login'); return }
    setStartingId(scenarioId)
    try {
      const session = await sessionsApi.create({ scenario_id: scenarioId })
      toast('Сессия жасалды!', 'success')
      navigate(`/session/${session.session_id}`)
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Сессия жасалмады', 'error')
    } finally {
      setStartingId(null)
    }
  }

  const v = getVisuals(profession)

  const diffDots = (n: number) =>
    Array.from({ length: 5 }, (_, i) => (
      <span
        key={i}
        style={{
          width: 7, height: 7, borderRadius: 2,
          background: i < n ? v.accent : 'rgba(124,58,237,0.15)',
          display: 'inline-block', marginRight: 2,
          transition: 'background 0.3s',
        }}
      />
    ))

  return (
    <div style={{ minHeight: '100vh', paddingBottom: 64, background: '#07040f', position: 'relative' }}>
      <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none" />

      {/* ── Hero banner ── */}
      <div style={{ position: 'relative', height: 260, overflow: 'hidden', marginBottom: 0 }}>
        {imgOk && profession ? (
          <img
            src={v.image}
            alt={profession.name}
            onError={() => setImgOk(false)}
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center 30%' }}
          />
        ) : (
          <div style={{ width: '100%', height: '100%', background: v.gradient }} />
        )}
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom,rgba(7,4,15,0.25) 0%,rgba(7,4,15,0.92) 100%)' }} />
        <Particles color={v.accent} count={16} />

        <div className="page-container" style={{ position: 'absolute', bottom: 28, left: 0, right: 0 }}>
          <button
            onClick={() => navigate('/professions')}
            style={{
              background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
              border: '1px solid rgba(255,255,255,0.15)',
              color: 'rgba(255,255,255,0.72)', cursor: 'pointer', fontSize: 13,
              marginBottom: 12, display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '5px 13px', borderRadius: 99,
            }}
          >
            ← Кәсіптерге оралу
          </button>

          {profession && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ display: 'flex', alignItems: 'center', gap: 14 }}
            >
              <div style={{
                width: 52, height: 52, borderRadius: 16,
                background: 'rgba(7,4,15,0.72)', backdropFilter: 'blur(12px)',
                border: `1px solid ${v.accent}50`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
              }}>
                {profession.icon_key ?? '⭐'}
              </div>
              <div>
                <h1 style={{ fontSize: 'clamp(22px,3vw,34px)', fontWeight: 900, color: '#f5f0ff', margin: '0 0 3px', letterSpacing: '-0.02em' }}>
                  {profession.name}
                </h1>
                <p style={{ color: 'rgba(255,255,255,0.52)', margin: 0, fontSize: 13 }}>{v.tagline}</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* ── Scenarios list ── */}
      <div className="page-container" style={{ position: 'relative', zIndex: 1, paddingTop: 32 }}>
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton rounded-2xl" style={{ height: 90 }} />
            ))}
          </div>
        )}

        {!loading && scenarios.length > 0 && (
          <>
            <p style={{ fontSize: 13, color: '#7c6fa8', marginBottom: 20 }}>
              <span style={{ color: v.accent, fontWeight: 700 }}>{scenarios.length}</span> сценарий қолжетімді
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {scenarios.map((s, i) => (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className="bento"
                  style={{
                    display: 'flex', alignItems: 'center', gap: 22,
                    borderColor: startingId === s.id ? `${v.accent}60` : undefined,
                  }}
                >
                  {/* Difficulty visual */}
                  <div style={{
                    width: 76, height: 76, flexShrink: 0, borderRadius: 18,
                    background: `${v.accent}12`, border: `1px solid ${v.accent}30`,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 5,
                  }}>
                    <span style={{ fontSize: 22 }}>
                      {(['🔵', '🟡', '🟠', '🔴', '🟣'][s.difficulty - 1]) ?? '🔵'}
                    </span>
                    <div>{diffDots(s.difficulty)}</div>
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 5 }}>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f5f0ff', margin: 0 }}>{s.title}</h3>
                      <span style={{
                        fontSize: 11, color: '#7c6fa8',
                        background: 'rgba(124,58,237,0.1)', padding: '2px 9px', borderRadius: 6, flexShrink: 0,
                      }}>
                        {s.estimated_steps} қадам
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: '#7c6fa8', lineHeight: 1.55, margin: '0 0 9px' }}>{s.description}</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                      {(s.tags ?? []).map(tag => (
                        <span
                          key={tag}
                          style={{
                            fontSize: 11, color: v.accent,
                            background: `${v.accent}14`, border: `1px solid ${v.accent}28`,
                            padding: '2px 9px', borderRadius: 999,
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Action */}
                  <div style={{ flexShrink: 0 }}>
                    <Button
                      onClick={() => handleStart(s.id)}
                      disabled={!!startingId}
                      loading={startingId === s.id}
                    >
                      {startingId === s.id ? 'Жүктелуде...' : 'Бастау →'}
                    </Button>
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        )}

        {!loading && scenarios.length === 0 && (
          <div className="text-center py-20 text-ogma-muted">
            <p style={{ fontSize: 48, marginBottom: 12 }}>📋</p>
            <p>Бұл кәсіп үшін сценарийлер жоқ</p>
          </div>
        )}
      </div>
    </div>
  )
}
