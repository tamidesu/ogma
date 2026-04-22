import type { SkillScoreItem } from '../../types'
import ProgressBar from '../ui/ProgressBar'
import { motion } from 'framer-motion'

interface Props {
  skills: SkillScoreItem[]
}

const skillLabels: Record<string, string> = {
  confidence:       'Сенімділік',
  decision_quality: 'Шешім сапасы',
  risk_management:  'Тәуекел',
  leadership:       'Көшбасшылық',
  communication:    'Коммуникация',
  technical:        'Техникалық',
  creativity:       'Шығармашылық',
  empathy:          'Эмпатия',
}

export default function SkillChart({ skills }: Props) {
  if (skills.length === 0) {
    return (
      <div className="bento flex items-center justify-center h-40">
        <p className="text-sm text-ogma-muted text-center">
          Дағдылар деректері жоқ.<br />
          <span className="text-xs">Алғашқы сценарийді аяқтаңыз!</span>
        </p>
      </div>
    )
  }

  const sorted = [...skills].sort((a, b) => b.score - a.score).slice(0, 8)

  return (
    <div className="bento">
      <h3 className="text-sm font-semibold text-ogma-secondary mb-4 flex items-center gap-2">
        <span className="w-1.5 h-4 rounded-full bg-gradient-primary" />
        Дағдылар профилі
      </h3>
      <div className="flex flex-col gap-3">
        {sorted.map((s, i) => (
          <motion.div
            key={`${s.profession_id}-${s.skill_key}`}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <ProgressBar
              value={s.score}
              max={100}
              label={skillLabels[s.skill_key] ?? s.skill_key.replace(/_/g, ' ')}
              showValue
            />
          </motion.div>
        ))}
      </div>
    </div>
  )
}
