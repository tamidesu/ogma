import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { progressApi } from '../api/progress'
import type { ProgressResponse, SessionSummaryResponse } from '../types'
import XPCard from '../components/dashboard/XPCard'
import SkillChart from '../components/dashboard/SkillChart'
import SessionHistoryList from '../components/dashboard/SessionHistoryList'
import Button from '../components/ui/Button'

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      {children}
    </motion.div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [progress, setProgress] = useState<ProgressResponse | null>(null)
  const [sessions, setSessions] = useState<SessionSummaryResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    Promise.all([
      progressApi.myProgress(),
      progressApi.mySessions(10, 0),
    ]).then(([p, s]) => {
      setProgress(p)
      setSessions(s)
    }).finally(() => setLoading(false))
  }, [user, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-ogma-600 border-t-transparent animate-spin" />
          <p className="text-ogma-muted text-sm">Жүктелуде...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-10">
      <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none opacity-50" />
      <div className="page-container relative z-10">

        {/* Header */}
        <FadeIn>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-black text-ogma-text">
                Сәлем, <span className="gradient-text">{user?.display_name ?? user?.email.split('@')[0]}</span> 👋
              </h1>
              <p className="text-ogma-muted mt-1">Прогресіңізді қарап шығыңыз</p>
            </div>
            <Button onClick={() => navigate('/professions')}>
              Жаңа сессия →
            </Button>
          </div>
        </FadeIn>

        {/* Bento grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* XP card — spans 1 col */}
          <FadeIn delay={0.05}>
            {progress ? (
              <XPCard progress={progress} />
            ) : (
              <div className="bento skeleton h-48" />
            )}
          </FadeIn>

          {/* Skill chart — spans 2 cols */}
          <FadeIn delay={0.1} >
            <div className="lg:col-span-2">
              <SkillChart skills={progress?.skill_scores ?? []} />
            </div>
          </FadeIn>

          {/* Session history — spans full width */}
          <FadeIn delay={0.15} >
            <div className="lg:col-span-3">
              <SessionHistoryList sessions={sessions} />
            </div>
          </FadeIn>
        </div>
      </div>
    </div>
  )
}
