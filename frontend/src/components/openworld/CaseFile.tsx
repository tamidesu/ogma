/**
 * CaseFile — renders the brief's case_file_md as a document-styled modal.
 * Shown at session start; user clicks "Бастау" to dismiss and begin playing.
 */
import { motion } from 'framer-motion'
import type { BriefDetail } from '../../api/openWorld'

interface Props {
  brief: BriefDetail
  onBegin: () => void
}

// Minimal markdown renderer (just headings + bold + paragraphs)
function renderMd(md: string) {
  return md.split('\n').map((line, i) => {
    if (line.startsWith('## '))
      return <h2 key={i} className="text-ogma-text font-semibold text-base mt-4 mb-1">{line.slice(3)}</h2>
    if (line.startsWith('# '))
      return <h1 key={i} className="text-ogma-text font-bold text-lg mt-2 mb-2">{line.slice(2)}</h1>
    if (line.startsWith('**') && line.endsWith('**'))
      return <p key={i} className="text-ogma-secondary font-semibold text-sm">{line.slice(2, -2)}</p>
    if (line.trim() === '')
      return <div key={i} className="h-2" />
    // Inline bold
    const parts = line.split(/(\*\*[^*]+\*\*)/g)
    return (
      <p key={i} className="text-ogma-muted text-sm leading-relaxed">
        {parts.map((p, j) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={j} className="text-ogma-text font-medium">{p.slice(2, -2)}</strong>
            : <span key={j}>{p}</span>
        )}
      </p>
    )
  })
}

export default function CaseFile({ brief, onBegin }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ogma-bg/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        className="w-full max-w-2xl max-h-[88vh] flex flex-col
                   bg-ogma-surface border border-ogma-stroke rounded-2xl shadow-card-lg overflow-hidden"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-ogma-stroke bg-ogma-surface2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-ogma-muted text-xs uppercase tracking-widest mb-1">
                Науқастың картасы
              </p>
              <h2 className="text-ogma-text font-bold text-xl">{brief.title}</h2>
            </div>
            <div className="text-right text-xs text-ogma-muted space-y-0.5">
              <p>👤 {brief.npc_display_name}</p>
              <p className="text-ogma-disabled">{brief.npc_role}</p>
            </div>
          </div>
          <div className="flex gap-3 mt-3 text-xs text-ogma-muted">
            <span>⏱ ~{brief.estimated_turns} бетбұрыс</span>
            <span>🎯 Қиындық: {'★'.repeat(brief.difficulty)}{'☆'.repeat(5 - brief.difficulty)}</span>
            <span className="ml-auto text-ogma-600 font-medium">{brief.locale.toUpperCase()}</span>
          </div>
        </div>

        {/* Case file content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-1 font-mono text-[13px]
                        scrollbar-thin scrollbar-thumb-ogma-surface3 scrollbar-track-transparent">
          {renderMd(brief.case_file_md)}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-ogma-stroke bg-ogma-surface2 flex items-center justify-between">
          <p className="text-ogma-muted text-xs">
            Сіз ситуацияны оқып шықтыңыз. Бастауға дайынсыз?
          </p>
          <motion.button
            whileTap={{ scale: 0.96 }}
            onClick={onBegin}
            className="px-6 py-2.5 rounded-xl bg-gradient-primary text-white font-semibold
                       text-sm shadow-glow-sm hover:shadow-glow transition-all"
          >
            Бастау →
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  )
}
