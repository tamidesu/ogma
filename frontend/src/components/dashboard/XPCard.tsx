import { motion } from 'framer-motion'
import type { ProgressResponse } from '../../types'
import ProgressBar from '../ui/ProgressBar'

interface Props {
  progress: ProgressResponse
}

export default function XPCard({ progress }: Props) {
  const { level, xp_total, xp_to_next_level, scenarios_completed } = progress
  const xpForCurrentLevel = xp_total % (xp_to_next_level || 1)

  return (
    <div className="bento relative overflow-hidden">
      {/* background orb */}
      <div className="orb w-48 h-48 bg-ogma-600 opacity-10 -top-16 -right-16" />

      <div className="relative flex items-start gap-5">
        <div className="flex-shrink-0">
          <motion.div
            whileHover={{ rotate: 10, scale: 1.05 }}
            className="w-16 h-16 rounded-2xl bg-gradient-primary
                       flex items-center justify-center shadow-glow text-white text-xl font-black"
          >
            {level}
          </motion.div>
          <p className="text-xs text-ogma-muted text-center mt-1">Деңгей</p>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-2xl font-black text-ogma-text">{xp_total.toLocaleString()}</span>
            <span className="text-sm text-ogma-muted">XP</span>
          </div>
          <ProgressBar
            value={xpForCurrentLevel}
            max={xp_to_next_level}
            label={`Келесі деңгейге`}
            sublabel={`${xp_to_next_level - xpForCurrentLevel} XP қалды`}
            showValue
          />
        </div>
      </div>

      <div className="mt-5 pt-4 border-t border-ogma-600/15 grid grid-cols-2 gap-4">
        <div>
          <p className="text-2xl font-bold text-ogma-400">{scenarios_completed}</p>
          <p className="text-xs text-ogma-muted mt-0.5">Аяқталған сценарий</p>
        </div>
        <div>
          <p className="text-2xl font-bold gradient-text">{level}</p>
          <p className="text-xs text-ogma-muted mt-0.5">Ағымдағы деңгей</p>
        </div>
      </div>
    </div>
  )
}
