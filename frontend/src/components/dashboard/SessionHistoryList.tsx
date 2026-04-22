import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import type { SessionSummaryResponse } from '../../types'
import Badge from '../ui/Badge'

interface Props {
  sessions: SessionSummaryResponse[]
}

const statusLabel: Record<string, string> = {
  completed: 'Аяқталған',
  active:    'Белсенді',
  paused:    'Кідіртілген',
  abandoned: 'Тасталған',
}
const statusVariant: Record<string, 'success' | 'info' | 'warning' | 'error'> = {
  completed: 'success',
  active:    'info',
  paused:    'warning',
  abandoned: 'error',
}

export default function SessionHistoryList({ sessions }: Props) {
  const navigate = useNavigate()

  if (sessions.length === 0) {
    return (
      <div className="bento flex items-center justify-center h-36">
        <p className="text-sm text-ogma-muted">Сессиялар тарихы жоқ</p>
      </div>
    )
  }

  return (
    <div className="bento">
      <h3 className="text-sm font-semibold text-ogma-secondary mb-4 flex items-center gap-2">
        <span className="w-1.5 h-4 rounded-full bg-gradient-to-b from-ogma-accent to-ogma-600" />
        Сессиялар тарихы
      </h3>
      <div className="flex flex-col divide-y divide-ogma-600/10">
        {sessions.map((s, i) => (
          <motion.div
            key={s.session_id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.05 }}
            className="py-3 first:pt-0 last:pb-0 flex items-center gap-3 cursor-pointer group"
            onClick={() => s.status === 'active' || s.status === 'paused'
              ? navigate(`/session/${s.session_id}`)
              : navigate(`/session/${s.session_id}/results`)}
          >
            <div className="flex-1 min-w-0">
              <p className="text-xs text-ogma-muted truncate font-mono">
                {s.session_id.slice(0, 8)}…
              </p>
              <p className="text-xs text-ogma-disabled mt-0.5">
                {new Date(s.started_at).toLocaleDateString('kk-KZ')}
              </p>
            </div>

            <Badge variant={statusVariant[s.status] ?? 'info'} dot>
              {statusLabel[s.status] ?? s.status}
            </Badge>

            {s.final_score !== null && (
              <span className="text-sm font-bold text-ogma-400">
                {Math.round(s.final_score)}
              </span>
            )}

            <span className="text-ogma-muted group-hover:text-ogma-400 transition-colors text-xs">→</span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
