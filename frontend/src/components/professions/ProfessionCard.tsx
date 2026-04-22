import { useState } from 'react'
import { motion } from 'framer-motion'
import type { ProfessionResponse } from '../../types'
import { getVisuals } from '../../lib/professionVisuals'
import Badge from '../ui/Badge'
import Particles from '../common/Particles'

interface Props {
  profession: ProfessionResponse
  index: number
  onSelect: (p: ProfessionResponse) => void
}

function diffVariant(label: string | null): 'success' | 'info' | 'warning' {
  if (!label) return 'info'
  const l = label.toLowerCase()
  if (['оңай', 'beginner', 'easy'].includes(l)) return 'success'
  if (['қиын', 'advanced', 'hard'].includes(l)) return 'warning'
  return 'info'
}

export default function ProfessionCard({ profession, index, onSelect }: Props) {
  const v = getVisuals(profession)
  const [imgOk, setImgOk] = useState(true)
  const [hovered, setHovered] = useState(false)
  const diffLabel = profession.difficulty_label ?? 'Орташа'

  return (
    <motion.div
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.45 }}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      whileHover={{ y: -6, scale: 1.01 }}
      onClick={() => onSelect(profession)}
      style={{
        borderRadius: 20,
        border: `1px solid ${hovered ? v.accent + '60' : 'rgba(124,58,237,0.18)'}`,
        background: 'rgba(13,8,32,0.85)',
        boxShadow: hovered
          ? `0 20px 60px rgba(0,0,0,0.6), 0 0 40px ${v.accent}25`
          : '0 4px 20px rgba(0,0,0,0.4)',
        transition: 'border-color 0.3s, box-shadow 0.3s',
        cursor: 'pointer',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* ── Image area ── */}
      <div style={{ position: 'relative', height: 180, overflow: 'hidden', flexShrink: 0 }}>
        {imgOk ? (
          <motion.img
            src={v.image}
            alt={profession.name}
            onError={() => setImgOk(false)}
            animate={{ scale: hovered ? 1.08 : 1 }}
            transition={{ duration: 0.5 }}
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'center', display: 'block' }}
          />
        ) : (
          <div style={{ width: '100%', height: '100%', background: v.gradient }} />
        )}

        {/* Gradient overlay */}
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom,rgba(7,4,15,0.08) 0%,rgba(7,4,15,0.72) 100%)' }} />

        {/* Particles on hover */}
        {hovered && <Particles color={v.accent} count={10} />}

        {/* Difficulty badge */}
        <div style={{ position: 'absolute', top: 14, right: 14 }}>
          <Badge variant={diffVariant(diffLabel)}>{diffLabel}</Badge>
        </div>

        {/* Icon */}
        <div style={{
          position: 'absolute', bottom: 16, left: 16,
          width: 46, height: 46, borderRadius: 13,
          background: 'rgba(7,4,15,0.72)', backdropFilter: 'blur(12px)',
          border: `1px solid ${v.accent}45`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22,
        }}>
          {profession.icon_key ?? '⭐'}
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{ padding: '18px 20px 20px', flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div>
          <h3 style={{ fontSize: 17, fontWeight: 800, color: '#f5f0ff', margin: '0 0 5px', letterSpacing: '-0.02em' }}>
            {profession.name}
          </h3>
          <p style={{ fontSize: 12, color: '#7c6fa8', lineHeight: 1.5, margin: 0 }}>{v.tagline}</p>
        </div>

        {/* Skill preview bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {v.skills.slice(0, 3).map(sk => (
            <div key={sk.name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ flex: 1, height: 3, background: 'rgba(124,58,237,0.12)', borderRadius: 99, overflow: 'hidden' }}>
                <motion.div
                  animate={{ width: hovered ? `${sk.score}%` : '0%' }}
                  transition={{ duration: 0.7, ease: [0, 0, 0.2, 1] }}
                  style={{ height: '100%', background: v.gradient, borderRadius: 99 }}
                />
              </div>
              <span style={{ fontSize: 10, color: '#7c6fa8', minWidth: 80, textAlign: 'right' }}>{sk.name}</span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <span style={{ fontSize: 12, color: '#f59e0b' }}>
              {'★'.repeat(Math.round(v.rating))}{'☆'.repeat(5 - Math.round(v.rating))}
            </span>
            <span style={{ fontSize: 11, color: '#7c6fa8', marginLeft: 3 }}>{v.rating}</span>
          </div>
          <span style={{ fontSize: 13, fontWeight: 700, color: v.accent }}>Таңдау →</span>
        </div>
      </div>
    </motion.div>
  )
}
