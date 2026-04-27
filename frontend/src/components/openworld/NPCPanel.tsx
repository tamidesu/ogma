/**
 * NPCPanel — unified NPC character panel.
 * Shows avatar, emotion bars (trust/fear/anger/hope), last utterance,
 * body-language footnote, and state label.
 */
import { AnimatePresence, motion } from 'framer-motion'

interface Props {
  displayName: string
  role: string
  avatarImageId?: string
  emotion: Record<string, number>
  stateLabel: string
  utterance: string
  bodyLanguage: string
  isStreaming?: boolean
}

const EMOTION_CONFIG: Array<{ key: string; label: string; color: string }> = [
  { key: 'trust',  label: 'Сенім',   color: '#10b981' },
  { key: 'hope',   label: 'Үміт',    color: '#3b82f6' },
  { key: 'fear',   label: 'Қорқыныш', color: '#f59e0b' },
  { key: 'anger',  label: 'Ашу',     color: '#ef4444' },
]

function EmotionBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-ogma-muted shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-ogma-surface3 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          animate={{ width: `${Math.max(2, value)}%` }}
          transition={{ type: 'spring', damping: 18, stiffness: 220 }}
        />
      </div>
      <span className="w-6 text-right text-ogma-disabled tabular-nums">{value}</span>
    </div>
  )
}

export default function NPCPanel({
  displayName,
  role,
  emotion,
  stateLabel,
  utterance,
  bodyLanguage,
  isStreaming,
}: Props) {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl bg-ogma-surface border border-ogma-stroke h-full">
      {/* Header */}
      <div className="flex items-start gap-3">
        {/* Avatar placeholder (actual avatar images referenced via image library) */}
        <div
          className="w-12 h-12 rounded-full bg-ogma-surface3 flex items-center justify-center
                     text-xl border border-ogma-stroke shrink-0 shadow-glow-sm overflow-hidden"
        >
          <span className="opacity-60">👤</span>
        </div>
        <div className="min-w-0">
          <p className="font-semibold text-ogma-text text-sm truncate">{displayName}</p>
          <p className="text-ogma-muted text-xs truncate">{role}</p>
          {stateLabel && (
            <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px]
                             bg-ogma-surface3 text-ogma-secondary border border-ogma-stroke">
              {stateLabel.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Emotion bars */}
      <div className="space-y-1.5">
        {EMOTION_CONFIG.map(({ key, label, color }) => (
          <EmotionBar
            key={key}
            label={label}
            value={emotion[key] ?? 50}
            color={color}
          />
        ))}
      </div>

      {/* Utterance bubble */}
      <AnimatePresence mode="wait">
        {utterance && (
          <motion.div
            key={utterance}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.35 }}
            className="relative rounded-lg bg-ogma-surface2 border border-ogma-stroke p-3"
          >
            {/* Speech bubble tail */}
            <div className="absolute -top-2 left-5 w-3 h-3 rotate-45
                            bg-ogma-surface2 border-l border-t border-ogma-stroke" />
            <p className="text-ogma-text text-sm leading-relaxed">
              {utterance}
            </p>
            {bodyLanguage && (
              <p className="mt-1.5 text-ogma-muted text-xs italic">
                {bodyLanguage}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Streaming indicator */}
      {isStreaming && !utterance && (
        <div className="flex items-center gap-1.5 text-ogma-muted text-xs">
          <span className="flex gap-0.5">
            {[0, 1, 2].map(i => (
              <span
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-ogma-600 animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </span>
          <span>Жауап беруде...</span>
        </div>
      )}
    </div>
  )
}
