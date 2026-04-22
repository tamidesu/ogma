import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { DecisionResponse } from '../../types'
import type { ProfessionCharacter, CharacterStatus } from '../../lib/professionVisuals'
import { statusFromScore } from '../../lib/professionVisuals'
import CharacterCard from './CharacterCard'

interface Props {
  decision: DecisionResponse
  characters: ProfessionCharacter[]
  onContinue: () => void
}

type ConsequenceType = 'excellent' | 'good' | 'warn' | 'critical'

function scoreToType(score: number): ConsequenceType {
  if (score >= 0.8) return 'excellent'
  if (score >= 0.6) return 'good'
  if (score >= 0.4) return 'warn'
  return 'critical'
}

const TYPE_CFG: Record<ConsequenceType, { bg: string; border: string; glow: string; titleColor: string; label: string }> = {
  excellent: {
    bg:         'linear-gradient(135deg,rgba(16,185,129,0.25),rgba(7,4,15,0.95))',
    border:     'rgba(16,185,129,0.4)',
    glow:       'rgba(16,185,129,0.3)',
    titleColor: '#10b981',
    label:      'Тамаша шешім!',
  },
  good: {
    bg:         'linear-gradient(135deg,rgba(59,130,246,0.2),rgba(7,4,15,0.95))',
    border:     'rgba(59,130,246,0.4)',
    glow:       'rgba(59,130,246,0.25)',
    titleColor: '#3b82f6',
    label:      'Жақсы шешім',
  },
  warn: {
    bg:         'linear-gradient(135deg,rgba(245,158,11,0.2),rgba(7,4,15,0.95))',
    border:     'rgba(245,158,11,0.4)',
    glow:       'rgba(245,158,11,0.25)',
    titleColor: '#f59e0b',
    label:      'Жақсартуға болады',
  },
  critical: {
    bg:         'linear-gradient(135deg,rgba(239,68,68,0.3),rgba(7,4,15,0.95))',
    border:     'rgba(239,68,68,0.5)',
    glow:       'rgba(239,68,68,0.4)',
    titleColor: '#ef4444',
    label:      'Қате шешім',
  },
}

const TYPE_ICON: Record<ConsequenceType, string> = {
  excellent: '🏆',
  good:      '✅',
  warn:      '⚠️',
  critical:  '💀',
}

export default function ConsequenceOverlay({ decision, characters, onContinue }: Props) {
  const [show, setShow] = useState(false)
  useEffect(() => { setTimeout(() => setShow(true), 80) }, [])

  const type = scoreToType(decision.step_score)
  const cfg = TYPE_CFG[type]
  const score = Math.round(decision.step_score * 100)
  const charStatus: CharacterStatus = statusFromScore(decision.step_score)
  const isCritical = type === 'critical'

  const charRows = characters.map(c => ({ ...c, status: charStatus }))

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 5000,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
        background: 'rgba(7,4,15,0.88)', backdropFilter: 'blur(16px)',
        opacity: show ? 1 : 0, transition: 'opacity 0.3s ease',
      }}
    >
      <motion.div
        initial={{ scale: 0.82, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', damping: 22, stiffness: 280 }}
        style={{
          width: '100%', maxWidth: 680,
          borderRadius: 28,
          background: cfg.bg,
          border: `1px solid ${cfg.border}`,
          boxShadow: `0 32px 80px rgba(0,0,0,0.8), 0 0 60px ${cfg.glow}`,
          overflow: 'hidden',
        }}
      >
        {/* Dramatic banner for critical decisions */}
        {isCritical && (
          <div
            style={{
              background: 'linear-gradient(90deg,rgba(239,68,68,0.4),rgba(239,68,68,0.1))',
              padding: '12px 32px', textAlign: 'center',
              borderBottom: '1px solid rgba(239,68,68,0.3)',
              animation: 'dramaticFlash 0.5s ease-in-out 3',
            }}
          >
            <p style={{ fontSize: 24, fontWeight: 900, color: '#ef4444', letterSpacing: '0.1em', margin: 0, textShadow: '0 0 20px rgba(239,68,68,0.8)' }}>
              CRITICAL DECISION
            </p>
            <p style={{ fontSize: 12, color: 'rgba(239,68,68,0.8)', margin: '3px 0 0' }}>Шешімді қайта қараңыз</p>
          </div>
        )}

        <div style={{ padding: 34 }}>
          {/* Icon + Score */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginBottom: 18 }}>
            <motion.div
              initial={{ scale: 0, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.15, type: 'spring', stiffness: 260, damping: 16 }}
              style={{ fontSize: 50, flexShrink: 0, lineHeight: 1 }}
            >
              {TYPE_ICON[type]}
            </motion.div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
                <span style={{ fontSize: 32, fontWeight: 900, color: cfg.titleColor }}>{score}</span>
                <span style={{ fontSize: 14, color: '#7c6fa8' }}>/ 100 — {cfg.label}</span>
              </div>
              <p style={{ fontSize: 13, color: '#c4b5fd', lineHeight: 1.55, margin: 0 }}>
                {decision.ai_feedback?.text
                  ? decision.ai_feedback.text.slice(0, 120) + (decision.ai_feedback.text.length > 120 ? '…' : '')
                  : `Қадам баллы: ${score}/100. ${cfg.label}.`
                }
              </p>
            </div>
          </div>

          {/* XP + Level up */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '7px 14px', borderRadius: 99,
              background: decision.xp_gained >= 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              border: `1px solid ${decision.xp_gained >= 0 ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'}`,
            }}>
              <span style={{ fontSize: 14, fontWeight: 800, color: decision.xp_gained >= 0 ? '#10b981' : '#ef4444' }}>
                {decision.xp_gained >= 0 ? '+' : ''}{decision.xp_gained} XP
              </span>
            </div>

            {decision.leveled_up && (
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '7px 14px', borderRadius: 99,
                background: 'rgba(232,121,249,0.15)',
                border: '1px solid rgba(232,121,249,0.4)',
              }}>
                <span style={{ fontSize: 14 }}>🎉</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#e879f9' }}>Деңгей артты!</span>
              </div>
            )}

            {decision.skills_earned.length > 0 && (
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                padding: '7px 14px', borderRadius: 99,
                background: 'rgba(59,130,246,0.15)',
                border: '1px solid rgba(59,130,246,0.35)',
              }}>
                <span style={{ fontSize: 12, color: '#3b82f6', fontWeight: 600 }}>
                  +{decision.skills_earned.length} дағды
                </span>
              </div>
            )}
          </div>

          {/* Character reactions */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
            {charRows.map(c => (
              <CharacterCard key={c.id} char={c} />
            ))}
          </div>

          {/* Metric deltas */}
          {Object.keys(decision.metrics_after).length > 0 && (
            <div
              style={{
                display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20,
                padding: '12px 16px', borderRadius: 14,
                background: 'rgba(20,15,46,0.6)', border: '1px solid rgba(124,58,237,0.15)',
              }}
            >
              {Object.entries(decision.metrics_after).map(([key, val]) => {
                const before = decision.metrics_before[key] ?? val
                const delta = val - before
                return (
                  <div key={key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 58 }}>
                    <span style={{ fontSize: 10, color: '#7c6fa8', marginBottom: 2, textTransform: 'capitalize' }}>{key}</span>
                    {delta !== 0 ? (
                      <span style={{ fontSize: 12, fontWeight: 700, color: delta > 0 ? '#10b981' : '#ef4444' }}>
                        {delta > 0 ? '+' : ''}{delta.toFixed(0)}
                      </span>
                    ) : (
                      <span style={{ fontSize: 12, color: '#4a4065' }}>—</span>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {/* Continue button */}
          <button
            onClick={onContinue}
            style={{
              width: '100%', padding: '14px', borderRadius: 14, fontSize: 15, fontWeight: 700,
              background: 'linear-gradient(135deg,#7c3aed,#e879f9)', color: '#fff', border: 'none', cursor: 'pointer',
              boxShadow: '0 0 24px rgba(124,58,237,0.4)', transition: 'filter 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.filter = 'brightness(1.12)')}
            onMouseLeave={e => (e.currentTarget.style.filter = '')}
          >
            {decision.is_terminal ? 'Нәтижелерді көру 🏆' : 'Жалғастыру →'}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
