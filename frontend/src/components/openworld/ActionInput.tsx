/**
 * ActionInput — free-text action input + AI-suggested chips.
 * Locked while streaming. Chips instantly populate the textarea on click.
 */
import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

interface Props {
  onSubmit: (text: string) => void
  suggestedActions: string[]
  isStreaming: boolean
  isTerminal: boolean
  locale?: string
}

const PLACEHOLDER_BY_LOCALE: Record<string, string> = {
  kk: 'Не жасайсыз? Мысалы: «Анамнез алу», «КТ тағайындау»...',
  ru: 'Что вы делаете? Например: «Собрать анамнез», «Назначить КТ»...',
  en: 'What do you do? e.g. "Take history", "Order chest CT"...',
}

export default function ActionInput({ onSubmit, suggestedActions, isStreaming, isTerminal, locale = 'kk' }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const canSubmit = text.trim().length > 0 && !isStreaming && !isTerminal

  function handleSubmit() {
    if (!canSubmit) return
    onSubmit(text.trim())
    setText('')
    textareaRef.current?.focus()
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [text])

  return (
    <div className="space-y-3">
      {/* Chips */}
      {suggestedActions.length > 0 && !isTerminal && (
        <motion.div
          className="flex flex-wrap gap-2"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          {suggestedActions.map((action, i) => (
            <motion.button
              key={action}
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => setText(action)}
              disabled={isStreaming || isTerminal}
              className="px-3 py-1.5 rounded-full text-sm border border-ogma-stroke
                         bg-ogma-surface2 text-ogma-secondary hover:bg-ogma-surface3
                         hover:border-ogma-600 hover:text-ogma-text transition-all
                         disabled:opacity-40 disabled:cursor-not-allowed
                         whitespace-nowrap"
            >
              {action}
            </motion.button>
          ))}
        </motion.div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={PLACEHOLDER_BY_LOCALE[locale] ?? PLACEHOLDER_BY_LOCALE.en}
            disabled={isStreaming || isTerminal}
            rows={1}
            className="w-full resize-none rounded-xl bg-ogma-surface2 border border-ogma-stroke
                       text-ogma-text placeholder:text-ogma-disabled px-4 py-3 pr-4
                       focus:outline-none focus:border-ogma-600 focus:ring-1 focus:ring-ogma-600/30
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-sm leading-relaxed transition-all max-h-36 overflow-y-auto"
          />
        </div>

        <motion.button
          onClick={handleSubmit}
          disabled={!canSubmit}
          whileTap={{ scale: 0.95 }}
          className="shrink-0 px-5 py-3 rounded-xl bg-gradient-primary text-white font-semibold
                     text-sm shadow-glow-sm hover:shadow-glow transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
                     flex items-center gap-2"
        >
          {isStreaming ? (
            <>
              <span className="flex gap-0.5">
                {[0, 1, 2].map(i => (
                  <span key={i} className="w-1 h-1 rounded-full bg-white/80 animate-bounce"
                        style={{ animationDelay: `${i * 0.12}s` }} />
                ))}
              </span>
              <span>...</span>
            </>
          ) : (
            <span>Жіберу</span>
          )}
        </motion.button>
      </div>

      {isTerminal && (
        <p className="text-center text-ogma-muted text-sm">
          Сессия аяқталды — нәтижелерді тексеріңіз.
        </p>
      )}
    </div>
  )
}
