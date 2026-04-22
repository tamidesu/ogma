import { motion } from 'framer-motion'
import type { ScenarioSummaryResponse } from '../../types'
import Badge from '../ui/Badge'
import Button from '../ui/Button'

interface Props {
  scenario: ScenarioSummaryResponse
  index: number
  onStart: (scenarioId: string) => void
  loading?: boolean
}

const difficultyLabel: Record<number, string> = {
  1: 'Оңай',
  2: 'Жеңіл',
  3: 'Орташа',
  4: 'Күрделі',
  5: 'Сарапшы',
}

const difficultyVariant = ['success', 'success', 'info', 'warning', 'error'] as const

export default function ScenarioCard({ scenario, index, onStart, loading }: Props) {
  const diff = Math.min(5, Math.max(1, scenario.difficulty))

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.4 }}
      className="bento flex flex-col gap-4 group hover:border-ogma-600/50 transition-colors duration-300"
    >
      <div>
        <div className="flex items-start justify-between gap-3 mb-2">
          <h3 className="text-base font-bold text-ogma-text group-hover:text-ogma-400
                         transition-colors duration-200 leading-snug">
            {scenario.title}
          </h3>
          <Badge variant={difficultyVariant[diff - 1]}>
            {difficultyLabel[diff]}
          </Badge>
        </div>
        <p className="text-sm text-ogma-muted line-clamp-3">{scenario.description}</p>
      </div>

      <div className="flex items-center gap-4 text-xs text-ogma-muted">
        <span className="flex items-center gap-1">
          <span className="text-ogma-600">◆</span>
          {scenario.estimated_steps} қадам
        </span>
        <span className="flex items-center gap-1">
          <span className="text-ogma-accent">★</span>
          {Array.from({ length: 5 }).map((_, i) => (
            <span key={i} className={i < diff ? 'text-ogma-400' : 'text-ogma-disabled'}>•</span>
          ))}
        </span>
      </div>

      {scenario.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {scenario.tags.slice(0, 4).map(tag => (
            <span key={tag} className="tag-pill">{tag}</span>
          ))}
        </div>
      )}

      <Button
        size="sm"
        className="w-full mt-auto"
        loading={loading}
        onClick={() => onStart(scenario.id)}
      >
        Бастау
      </Button>
    </motion.div>
  )
}
