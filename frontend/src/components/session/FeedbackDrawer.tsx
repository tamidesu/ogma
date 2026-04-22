import { motion } from 'framer-motion'
import Drawer from '../ui/Drawer'
import type { AIFeedbackResponse, DecisionResponse } from '../../types'
import Badge from '../ui/Badge'

interface Props {
  open: boolean
  onClose: () => void
  decision: DecisionResponse | null
}

const toneVariant: Record<string, 'success' | 'warning' | 'info'> = {
  encouraging: 'success',
  critical:    'warning',
  neutral:     'info',
}
const toneLabel: Record<string, string> = {
  encouraging: 'Мадақтау',
  critical:    'Сын',
  neutral:     'Бейтарап',
}

function FeedbackSection({ title, content, icon }: { title: string; content: string; icon: string }) {
  return (
    <div className="bento">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-base">{icon}</span>
        <h4 className="text-sm font-semibold text-ogma-secondary">{title}</h4>
      </div>
      <p className="text-sm text-ogma-text leading-relaxed">{content}</p>
    </div>
  )
}

function AIFeedback({ feedback }: { feedback: AIFeedbackResponse }) {
  return (
    <div className="flex flex-col gap-3">
      {feedback.tone && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-ogma-muted">Тон:</span>
          <Badge variant={toneVariant[feedback.tone] ?? 'info'} dot>
            {toneLabel[feedback.tone] ?? feedback.tone}
          </Badge>
        </div>
      )}

      {feedback.text && (
        <div className="p-4 rounded-xl bg-ogma-600/10 border border-ogma-600/25">
          <p className="text-sm text-ogma-text leading-relaxed">{feedback.text}</p>
        </div>
      )}

      {feedback.key_insight && (
        <FeedbackSection title="Негізгі түсінік" content={feedback.key_insight} icon="💡" />
      )}
      {feedback.consequence_analysis && (
        <FeedbackSection title="Салдарды талдау" content={feedback.consequence_analysis} icon="📊" />
      )}
      {feedback.coaching_question && (
        <FeedbackSection title="Коучинг сұрағы" content={feedback.coaching_question} icon="🤔" />
      )}
      {feedback.alternative_path && (
        <FeedbackSection title="Балама жол" content={feedback.alternative_path} icon="🔀" />
      )}
    </div>
  )
}

export default function FeedbackDrawer({ open, onClose, decision }: Props) {
  return (
    <Drawer open={open} onClose={onClose} title="AI Талдауы">
      {decision ? (
        <div className="flex flex-col gap-5">
          {/* Score summary */}
          <div className="bento text-center">
            <p className="text-xs text-ogma-muted mb-1">Қадам баллы</p>
            <div className="text-4xl font-black gradient-text">
              {Math.round(decision.step_score * 100)}
            </div>
            <p className="text-xs text-ogma-muted mt-1">/ 100</p>
          </div>

          {/* XP & level */}
          <div className="flex gap-3">
            <div className="bento flex-1 text-center">
              <p className="text-xs text-ogma-muted">XP</p>
              <p className="text-2xl font-bold text-ogma-400 mt-1">+{decision.xp_gained}</p>
            </div>
            {decision.leveled_up && (
              <div className="bento flex-1 text-center bg-gradient-to-br from-ogma-600/20 to-ogma-accent/10">
                <p className="text-xs text-ogma-accent">Деңгей артты!</p>
                <p className="text-2xl font-bold text-ogma-accent mt-1">🎉</p>
              </div>
            )}
          </div>

          {/* Skills earned */}
          {decision.skills_earned.length > 0 && (
            <div className="bento">
              <h4 className="text-sm font-semibold text-ogma-secondary mb-3">Алынған дағдылар</h4>
              <div className="flex flex-col gap-2">
                {decision.skills_earned.map(s => (
                  <div key={s.skill} className="flex items-center justify-between">
                    <span className="text-sm text-ogma-text capitalize">{s.skill}</span>
                    <span className="text-xs font-semibold text-ogma-success">+{s.xp_gained.toFixed(1)} XP</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI Feedback */}
          {decision.ai_feedback.generated && (
            <>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-px bg-ogma-600/20" />
                <span className="text-xs text-ogma-muted px-2">AI Пікірі</span>
                <div className="flex-1 h-px bg-ogma-600/20" />
              </div>
              {decision.ai_feedback.text ? (
                <AIFeedback feedback={decision.ai_feedback} />
              ) : (
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="flex items-center justify-center gap-2 py-6 text-ogma-muted text-sm"
                >
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  AI пікірі жасалуда...
                </motion.div>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center h-40 text-ogma-muted text-sm">
          Шешім таңдалмаған
        </div>
      )}
    </Drawer>
  )
}
