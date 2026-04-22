import { motion } from 'framer-motion'

interface Props {
  value: number
  max?: number
  label?: string
  sublabel?: string
  color?: 'primary' | 'accent' | 'success' | 'warning'
  size?: 'sm' | 'md' | 'lg'
  showValue?: boolean
  animated?: boolean
}

const trackHeight: Record<NonNullable<Props['size']>, string> = {
  sm: 'h-1',
  md: 'h-1.5',
  lg: 'h-2.5',
}

const fillColor: Record<NonNullable<Props['color']>, string> = {
  primary: 'bg-gradient-primary',
  accent:  'bg-gradient-to-r from-ogma-accent to-ogma-400',
  success: 'bg-ogma-success',
  warning: 'bg-ogma-warning',
}

export default function ProgressBar({
  value,
  max = 100,
  label,
  sublabel,
  color = 'primary',
  size = 'md',
  showValue = false,
  animated = true,
}: Props) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && <span className="text-sm font-medium text-ogma-secondary">{label}</span>}
          <div className="flex items-center gap-2 ml-auto">
            {sublabel && <span className="text-xs text-ogma-muted">{sublabel}</span>}
            {showValue && (
              <span className="text-xs font-semibold text-ogma-400">{Math.round(pct)}%</span>
            )}
          </div>
        </div>
      )}
      <div className={`${trackHeight[size]} rounded-full bg-ogma-surface3 overflow-hidden`}>
        <motion.div
          className={`h-full rounded-full ${fillColor[color]}`}
          initial={animated ? { width: 0 } : false}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0, 0, 0.2, 1] }}
        />
      </div>
    </div>
  )
}
