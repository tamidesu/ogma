import { motion } from 'framer-motion'
import type { StepInfo } from '../../types'
import Badge from '../ui/Badge'

interface Props {
  step: StepInfo
  stepNumber: number
  totalSteps?: number
}

export default function StepDisplay({ step, stepNumber, totalSteps }: Props) {
  return (
    <motion.div
      key={step.step_key}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="bento"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-primary
                        flex items-center justify-center text-white text-sm font-bold shadow-glow-sm">
          {stepNumber}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-ogma-text leading-tight">{step.title}</h2>
            <Badge variant="default">{step.step_type === 'decision' ? 'Шешім' : step.step_type}</Badge>
          </div>
          {totalSteps && (
            <p className="text-xs text-ogma-muted mt-0.5">{stepNumber} / {totalSteps} қадам</p>
          )}
        </div>
      </div>

      <div className="relative">
        <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-primary rounded-full opacity-40" />
        <p className="pl-4 text-sm text-ogma-secondary leading-relaxed">{step.narrative}</p>
      </div>
    </motion.div>
  )
}
