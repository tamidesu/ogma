/**
 * TurnResultStrip — collapsible strip showing intent → validation → citations.
 * Appears after each turn, stagger-animates its sections.
 */
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { TurnSnapshot } from '../../hooks/useOpenWorldSession'

interface Props {
  turn: TurnSnapshot | null
  isStreaming: boolean
}

const SEVERITY_COLORS: Record<string, string> = {
  minor:    'text-ogma-success border-ogma-success/30 bg-ogma-success/10',
  moderate: 'text-ogma-warning border-ogma-warning/30 bg-ogma-warning/10',
  severe:   'text-ogma-error border-ogma-error/30 bg-ogma-error/10',
  critical: 'text-ogma-error border-ogma-error/50 bg-ogma-error/20',
}

export default function TurnResultStrip({ turn, isStreaming }: Props) {
  const [showCitations, setShowCitations] = useState(false)

  if (!turn?.intent) {
    if (isStreaming) {
      return (
        <div className="h-10 flex items-center px-4 gap-2 text-ogma-muted text-sm">
          <span className="flex gap-0.5">
            {[0,1,2].map(i => (
              <span key={i} className="w-1.5 h-1.5 rounded-full bg-ogma-600 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </span>
          <span>Агенттер жұмыс жасауда...</span>
        </div>
      )
    }
    return null
  }

  const { intent, validation } = turn
  const hasBlockedAction = validation?.blocks_action

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="px-4 py-3 rounded-xl bg-ogma-surface border border-ogma-stroke space-y-2"
    >
      {/* Row 1: intent */}
      <motion.div
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.05 }}
        className="flex items-center gap-2 text-sm"
      >
        <span className="text-ogma-muted shrink-0">Әрекет:</span>
        <span className="text-ogma-text font-medium">
          {intent.raw_paraphrase || `${intent.verb} → ${intent.target}`}
        </span>
        <span className={`ml-auto text-xs px-2 py-0.5 rounded-full border
          ${intent.plausibility >= 0.7 ? 'text-ogma-success border-ogma-success/30 bg-ogma-success/10'
            : 'text-ogma-warning border-ogma-warning/30 bg-ogma-warning/10'}`}>
          {Math.round(intent.plausibility * 100)}% анық
        </span>
      </motion.div>

      {/* Row 2: validation */}
      {validation && (
        <motion.div
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.13 }}
          className="flex items-center gap-2 flex-wrap text-sm"
        >
          <span className="text-ogma-muted shrink-0">Тексеру:</span>
          {hasBlockedAction ? (
            <span className="text-ogma-error font-medium">🚫 Тоқтатылды</span>
          ) : (
            <span className={`text-xs px-2 py-0.5 rounded-full border
              ${validation.is_standard_of_care
                ? 'text-ogma-success border-ogma-success/30 bg-ogma-success/10'
                : 'text-ogma-warning border-ogma-warning/30 bg-ogma-warning/10'}`}>
              {validation.is_standard_of_care ? '✓ Стандартқа сай' : '⚠ Стандарттан ауытқу'}
            </span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full border
            ${SEVERITY_COLORS[validation.severity_if_wrong] ?? 'text-ogma-muted border-ogma-stroke'}`}>
            {validation.severity_if_wrong}
          </span>
          {validation.coach_note && (
            <span className="text-ogma-muted text-xs italic ml-1 truncate max-w-xs">
              {validation.coach_note}
            </span>
          )}
          {validation.citations.length > 0 && (
            <button
              onClick={() => setShowCitations(v => !v)}
              className="ml-auto text-ogma-600 hover:text-ogma-accent text-xs underline-offset-2 hover:underline"
            >
              {validation.citations.length} сілтеме {showCitations ? '▲' : '▼'}
            </button>
          )}
        </motion.div>
      )}

      {/* Citations expandable */}
      <AnimatePresence>
        {showCitations && validation?.citations && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-2 pt-1 border-t border-ogma-stroke">
              {validation.citations.map((c, i) => (
                <div key={i} className="text-xs space-y-0.5">
                  <p className="text-ogma-secondary font-medium">{c.source}</p>
                  <p className="text-ogma-muted leading-relaxed">{c.snippet}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Row 3: complication badge */}
      {turn.world?.new_complication && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
          className="flex items-center gap-2 text-xs text-ogma-warning"
        >
          <span>⚡</span>
          <span>Жаңа асқыну: {turn.world.new_complication.narrative_hook as string}</span>
        </motion.div>
      )}
    </motion.div>
  )
}
