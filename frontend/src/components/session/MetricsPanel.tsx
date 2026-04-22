import { motion } from 'framer-motion'
import ProgressBar from '../ui/ProgressBar'

interface Props {
  metrics: Record<string, number>
  metricsBefore?: Record<string, number>
}

const METRIC_ICONS: Record<string, string> = {
  stress:           '😰',
  experience:       '🎯',
  time:             '⏱',
  resources:        '💎',
  trust:            '🤝',
  reputation:       '⭐',
  confidence:       '💪',
  decision_quality: '🎯',
  risk_management:  '🛡',
  leadership:       '👑',
  communication:    '💬',
  technical:        '⚙️',
  creativity:       '✨',
  empathy:          '❤️',
  efficiency:       '⚡',
  teamwork:         '👥',
  // Kazakh keys from prototype
  'Стресс':         '😰',
  'Тәжірибе':       '🎯',
  'Уақыт':          '⏱',
  'Ресурс':         '💎',
  'Сенім':          '🤝',
  'Беделі':         '⭐',
}

function metricLabel(key: string) {
  const labels: Record<string, string> = {
    confidence:       'Сенімділік',
    decision_quality: 'Шешім сапасы',
    risk_management:  'Тәуекел',
    leadership:       'Көшбасшылық',
    communication:    'Коммуникация',
    technical:        'Техникалық',
    creativity:       'Шығармашылық',
    empathy:          'Эмпатия',
    efficiency:       'Тиімділік',
    teamwork:         'Командалық жұмыс',
    stress:           'Стресс',
    experience:       'Тәжірибе',
    time:             'Уақыт',
    resources:        'Ресурс',
    trust:            'Сенім',
    reputation:       'Беделі',
  }
  return labels[key] ?? key.replace(/_/g, ' ')
}

export default function MetricsPanel({ metrics, metricsBefore }: Props) {
  const entries = Object.entries(metrics)

  if (entries.length === 0) {
    return (
      <div className="bento">
        <h3 className="text-sm font-semibold text-ogma-secondary mb-3 flex items-center gap-2">
          <span className="w-0.5 h-4 rounded-full bg-gradient-primary" />
          Метрикалар
        </h3>
        <p className="text-xs text-ogma-muted">Метрикалар жоқ</p>
      </div>
    )
  }

  return (
    <div className="bento">
      <h3 className="text-sm font-semibold text-ogma-secondary mb-4 flex items-center gap-2">
        <span className="w-0.5 h-4 rounded-full bg-gradient-primary inline-block" />
        Метрикалар
      </h3>
      <div className="flex flex-col gap-4">
        {entries.map(([key, value], i) => {
          const before = metricsBefore?.[key]
          // Backend sends 0-100 integer values directly
          const val  = Math.round(Math.max(0, Math.min(100, value)))
          const prev = before !== undefined ? Math.round(Math.max(0, Math.min(100, before))) : undefined
          const delta = prev !== undefined ? val - prev : undefined
          const icon = METRIC_ICONS[key] || '📊'

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium text-ogma-secondary flex items-center gap-1.5">
                  <span>{icon}</span>
                  {metricLabel(key)}
                </span>
                <div className="flex items-center gap-2">
                  {delta !== undefined && Math.abs(delta) > 0 && (
                    <span className={`text-xs font-semibold ${delta > 0 ? 'text-ogma-success' : 'text-ogma-error'}`}>
                      {delta > 0 ? '+' : ''}{delta}
                    </span>
                  )}
                  <span className="text-xs font-bold text-ogma-400">{val}</span>
                </div>
              </div>
              <ProgressBar value={val} max={100} animated />
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
