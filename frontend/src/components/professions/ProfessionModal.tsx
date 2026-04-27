import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { ProfessionResponse } from '../../types'
import { getVisuals } from '../../lib/professionVisuals'
import Particles from '../common/Particles'
import Badge from '../ui/Badge'

interface Props {
  profession: ProfessionResponse
  onClose: () => void
  onStart: () => void
}

function diffVariant(label: string | null): 'success' | 'info' | 'warning' {
  if (!label) return 'info'
  const l = label.toLowerCase()
  if (['оңай', 'beginner', 'easy'].includes(l)) return 'success'
  if (['қиын', 'advanced', 'hard'].includes(l)) return 'warning'
  return 'info'
}

export default function ProfessionModal({ profession, onClose, onStart }: Props) {
  const v = getVisuals(profession)
  const [imgOk, setImgOk] = useState(true)
  const [animSkills, setAnimSkills] = useState(false)
  const diffLabel = profession.difficulty_label ?? 'Орташа'

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    const t = setTimeout(() => setAnimSkills(true), 280)
    return () => {
      document.body.style.overflow = ''
      clearTimeout(t)
    }
  }, [])

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 3000,
          background: 'rgba(7,4,15,0.78)',
          backdropFilter: 'blur(10px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
        }}
      >
        <motion.div
          initial={{ scale: 0.88, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.88, opacity: 0 }}
          transition={{ type: 'spring', damping: 22, stiffness: 280 }}
          onClick={e => e.stopPropagation()}
          style={{
            width: '100%', maxWidth: 780, maxHeight: '90vh',
            overflowY: 'auto', borderRadius: 28,
            background: 'rgba(13,8,32,0.97)',
            border: `1px solid ${v.accent}35`,
            boxShadow: `0 32px 80px rgba(0,0,0,0.7), 0 0 60px ${v.accent}15`,
          }}
        >
          {/* ── Hero Image ── */}
          <div style={{ position: 'relative', height: 280, overflow: 'hidden', borderRadius: '28px 28px 0 0', flexShrink: 0 }}>
            {imgOk ? (
              <img
                src={v.image}
                alt={profession.name}
                onError={() => setImgOk(false)}
                style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center top', filter: v.imageFilter }}
              />
            ) : (
              <div style={{ width: '100%', height: '100%', background: v.gradient }} />
            )}
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom,rgba(7,4,15,0.12) 0%,rgba(7,4,15,0.88) 100%)' }} />
            <Particles color={v.accent} count={18} />

            {/* Close */}
            <button
              onClick={onClose}
              style={{
                position: 'absolute', top: 18, right: 18,
                width: 36, height: 36, borderRadius: '50%',
                background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255,255,255,0.15)',
                color: '#fff', fontSize: 18,
                display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
              }}
            >
              ✕
            </button>

            {/* Title overlay */}
            <div style={{ position: 'absolute', bottom: 26, left: 30, right: 30, display: 'flex', alignItems: 'flex-end', gap: 14 }}>
              <div style={{
                width: 62, height: 62, borderRadius: 18, flexShrink: 0,
                background: 'rgba(7,4,15,0.72)', backdropFilter: 'blur(16px)',
                border: `1px solid ${v.accent}50`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28,
              }}>
                {{ stethoscope: '🩺', code: '💻', scales: '⚖️', chart: '📊' }[profession.icon_key ?? ''] ?? profession.icon_key ?? '⭐'}
              </div>
              <div>
                <p style={{ fontSize: 11, color: v.accent, fontWeight: 700, margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Кәсіп</p>
                <h2 style={{ fontSize: 30, fontWeight: 900, color: '#f5f0ff', margin: 0, letterSpacing: '-0.03em' }}>{profession.name}</h2>
                <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.55)', margin: '3px 0 0' }}>{v.tagline}</p>
              </div>
            </div>
          </div>

          {/* ── Body ── */}
          <div style={{ padding: 32 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 26 }}>

              {/* Description + stats */}
              <div>
                <p style={{ fontSize: 11, color: '#7c6fa8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 10px' }}>Сипаттама</p>
                <p style={{ fontSize: 14, color: '#c4b5fd', lineHeight: 1.72, margin: 0 }}>
                  {profession.description || `${profession.name} кәсібінде нақты жағдайларды симуляциялаңыз, маңызды шешімдер қабылдаңыз және жасанды интеллект арқылы жеке кері байланыс алыңыз.`}
                </p>

                <div style={{ display: 'flex', gap: 20, marginTop: 18 }}>
                  {[
                    { label: 'Аяқталды', val: v.completions },
                    { label: 'Орт. уақыт', val: v.avgTime },
                    { label: 'Рейтинг', val: `${v.rating} ★` },
                  ].map(s => (
                    <div key={s.label}>
                      <p style={{ fontSize: 16, fontWeight: 800, color: '#f5f0ff', margin: '0 0 2px' }}>{s.val}</p>
                      <p style={{ fontSize: 11, color: '#7c6fa8', margin: 0 }}>{s.label}</p>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: 14 }}>
                  <Badge variant={diffVariant(diffLabel)}>{diffLabel}</Badge>
                </div>
              </div>

              {/* Skills */}
              <div>
                <p style={{ fontSize: 11, color: '#7c6fa8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 14px' }}>Дамитын дағдылар</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
                  {v.skills.map((sk, i) => (
                    <div key={sk.name}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                        <span style={{ fontSize: 13, color: '#c4b5fd' }}>{sk.name}</span>
                        <span style={{ fontSize: 12, fontWeight: 700, color: v.accent }}>{sk.score}</span>
                      </div>
                      <div style={{ height: 5, background: 'rgba(124,58,237,0.12)', borderRadius: 99, overflow: 'hidden' }}>
                        <motion.div
                          animate={{ width: animSkills ? `${sk.score}%` : '0%' }}
                          transition={{ duration: 0.85, delay: i * 0.1, ease: [0, 0, 0.2, 1] }}
                          style={{ height: '100%', background: v.gradient, borderRadius: 99 }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Scenario previews */}
            <div style={{
              padding: 18, borderRadius: 16,
              background: 'rgba(28,22,64,0.5)', border: '1px solid rgba(124,58,237,0.15)',
              marginBottom: 22,
            }}>
              <p style={{ fontSize: 11, color: '#7c6fa8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 12px' }}>Сценарийлер алдын-ала қарау</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                {v.preview.map((p, i) => (
                  <div key={p} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                      width: 24, height: 24, borderRadius: 8,
                      background: `${v.accent}20`, border: `1px solid ${v.accent}35`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 11, fontWeight: 800, color: v.accent, flexShrink: 0,
                    }}>
                      {i + 1}
                    </div>
                    <span style={{ fontSize: 14, color: '#c4b5fd' }}>{p}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA */}
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={onStart}
                style={{
                  flex: 1, padding: '13px 24px', borderRadius: 14,
                  fontSize: 15, fontWeight: 700,
                  background: v.gradient, color: '#fff', border: 'none', cursor: 'pointer',
                  boxShadow: `0 0 28px ${v.accent}40`, transition: 'filter 0.2s',
                }}
                onMouseEnter={e => (e.currentTarget.style.filter = 'brightness(1.1)')}
                onMouseLeave={e => (e.currentTarget.style.filter = '')}
              >
                Сценарийлерді қарау →
              </button>
              <button
                onClick={onClose}
                style={{
                  padding: '13px 20px', borderRadius: 14, fontSize: 14, fontWeight: 600,
                  background: 'rgba(28,22,64,0.7)', color: '#7c6fa8',
                  border: '1px solid rgba(124,58,237,0.2)', cursor: 'pointer',
                }}
              >
                Артқа
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
