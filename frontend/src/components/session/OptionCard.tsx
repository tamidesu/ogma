import { motion } from 'framer-motion'
import type { OptionInfo } from '../../types'

interface Props {
  option: OptionInfo
  index: number
  selected: boolean
  disabled: boolean
  onSelect: (key: string) => void
}

const optionLetters = ['А', 'Ä', 'Б', 'В', 'Г', 'Д']

export default function OptionCard({ option, index, selected, disabled, onSelect }: Props) {
  const isUnavailable = !option.is_available
  const isDisabled = disabled || isUnavailable

  return (
    <motion.button
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 }}
      whileHover={!isDisabled ? { x: 4, scale: 1.005 } : {}}
      whileTap={!isDisabled ? { scale: 0.99 } : {}}
      onClick={() => !isDisabled && onSelect(option.option_key)}
      disabled={isDisabled}
      className={`
        w-full text-left p-4 rounded-xl border transition-all duration-200
        flex items-start gap-3
        ${selected
          ? 'border-ogma-600 bg-ogma-600/20 shadow-glow-sm'
          : isUnavailable
            ? 'border-ogma-disabled/30 bg-ogma-surface/40 opacity-40 cursor-not-allowed'
            : 'border-ogma-600/20 bg-ogma-surface2/50 hover:border-ogma-600/50 hover:bg-ogma-surface2/80 cursor-pointer'
        }
        disabled:opacity-50 disabled:cursor-not-allowed
      `}
    >
      <div className={`
        flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center
        text-xs font-bold transition-colors duration-200
        ${selected
          ? 'bg-gradient-primary text-white shadow-glow-sm'
          : 'bg-ogma-surface3 text-ogma-muted border border-ogma-600/20'
        }
      `}>
        {optionLetters[index] ?? index + 1}
      </div>

      <div className="flex-1 min-w-0">
        <p className={`text-sm font-semibold leading-snug ${selected ? 'text-ogma-text' : 'text-ogma-secondary'}`}>
          {option.label}
        </p>
        {option.description && (
          <p className="mt-1 text-xs text-ogma-muted leading-relaxed">{option.description}</p>
        )}
        {isUnavailable && (
          <p className="mt-1 text-xs text-ogma-error">Қолжетімсіз</p>
        )}
      </div>
    </motion.button>
  )
}
