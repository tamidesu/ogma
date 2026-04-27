/**
 * WorldMetrics — compact metric bars for the open-world simulation.
 * Shows animated bars + optional complication indicator.
 */
import { motion } from 'framer-motion'

interface Props {
  metrics: Record<string, number>
  delta?: Record<string, number>
  elapsedMin?: number
  phase?: string
  turnIndex?: number
  maxTurns?: number
}

const METRIC_LABELS: Record<string, { label: string; emoji: string; color: string }> = {
  patient_stability:   { label: 'Тұрақтылық',    emoji: '❤️',  color: '#10b981' },
  diagnosis_accuracy:  { label: 'Диагноз',       emoji: '🔬',  color: '#3b82f6' },
  team_trust:          { label: 'Сенім',          emoji: '🤝',  color: '#8b5cf6' },
  score:               { label: 'Ұпай',           emoji: '⭐',  color: '#f59e0b' },
}

function MetricBar({
  metricKey,
  value,
  delta,
}: {
  metricKey: string
  value: number
  delta?: number
}) {
  const cfg = METRIC_LABELS[metricKey]
  const label = cfg?.label ?? metricKey.replace(/_/g, ' ')
  const color = cfg?.color ?? '#7c3aed'
  const emoji = cfg?.emoji ?? '📊'

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-ogma-muted flex items-center gap-1">
          <span>{emoji}</span>
          <span>{label}</span>
        </span>
        <div className="flex items-center gap-1.5">
          {delta !== undefined && delta !== 0 && (
            <motion.span
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className={`text-[10px] font-semibold ${delta > 0 ? 'text-ogma-success' : 'text-ogma-error'}`}
            >
              {delta > 0 ? `+${delta}` : delta}
            </motion.span>
          )}
          <span className="text-xs text-ogma-text font-semibold tabular-nums">{Math.round(value)}</span>
        </div>
      </div>
      <div className="h-1.5 bg-ogma-surface3 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          animate={{ width: `${Math.max(1, value)}%` }}
          transition={{ type: 'spring', damping: 20, stiffness: 200 }}
        />
      </div>
    </div>
  )
}

export default function WorldMetrics({ metrics, delta = {}, elapsedMin = 0, phase, turnIndex, maxTurns }: Props) {
  const hours = Math.floor(elapsedMin / 60)
  const mins = elapsedMin % 60
  const timeStr = hours > 0 ? `${hours}ч ${mins}м` : `${mins} мин`

  return (
    <div className="p-4 rounded-xl bg-ogma-surface border border-ogma-stroke space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-ogma-muted uppercase tracking-widest">
          Дүние
        </span>
        <div className="text-right text-xs text-ogma-muted space-y-0.5">
          <p>⏱ {timeStr}</p>
          {turnIndex !== undefined && maxTurns && (
            <p className="text-ogma-disabled">{turnIndex}/{maxTurns} бетбұрыс</p>
          )}
        </div>
      </div>

      {phase && (
        <p className="text-[10px] text-ogma-600 uppercase tracking-wider font-medium">
          {phase.replace(/_/g, ' ')}
        </p>
      )}

      <div className="space-y-2.5">
        {Object.entries(metrics)
          .filter(([k]) => k !== 'score' || metrics[k] > 0)
          .map(([k, v]) => (
            <MetricBar key={k} metricKey={k} value={v} delta={delta[k]} />
          ))}
      </div>
    </div>
  )
}
