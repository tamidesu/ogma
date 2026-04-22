import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { professionsApi } from '../api/professions'
import type { ProfessionResponse } from '../types'
import ProfessionCard from '../components/professions/ProfessionCard'
import ProfessionModal from '../components/professions/ProfessionModal'

export default function ProfessionsPage() {
  const navigate = useNavigate()
  const [professions, setProfessions] = useState<ProfessionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<ProfessionResponse | null>(null)

  useEffect(() => {
    professionsApi.list()
      .then(setProfessions)
      .catch(err => setError(err instanceof Error ? err.message : 'Қате орын алды'))
      .finally(() => setLoading(false))
  }, [])

  function handleStart() {
    if (!selected) return
    setSelected(null)
    navigate(`/professions/${selected.id}/scenarios`)
  }

  return (
    <div className="min-h-screen py-12 relative" style={{ background: '#07040f' }}>
      <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none" />
      <div className="orb w-[500px] h-[500px] bg-ogma-600 opacity-[0.06] top-[-100px] right-[-150px]" />

      <div className="page-container relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-14"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                          border border-ogma-600/30 bg-ogma-600/10 text-ogma-400
                          text-xs font-semibold mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-ogma-accent animate-pulse" />
            {loading ? 'Жүктелуде...' : `${professions.length} кәсіп қолжетімді`}
          </div>
          <h1 className="text-5xl font-black tracking-tight mb-3">
            <span className="gradient-text">Кәсіптер</span>
          </h1>
          <p className="text-ogma-muted text-base">Өз кәсібіңізді таңдаңыз және дағдыларыңызды дамытыңыз</p>
        </motion.div>

        {/* Error */}
        {error && (
          <div className="bento border-ogma-error/30 bg-ogma-error/10 text-ogma-error text-sm text-center mb-8">
            {error}
          </div>
        )}

        {/* Skeletons */}
        {loading && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton rounded-2xl" style={{ height: 340 }} />
            ))}
          </div>
        )}

        {/* Grid */}
        {!loading && professions.length > 0 && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {professions.map((p, i) => (
              <ProfessionCard key={p.id} profession={p} index={i} onSelect={setSelected} />
            ))}
          </div>
        )}

        {!loading && professions.length === 0 && !error && (
          <div className="text-center py-24 text-ogma-muted">
            <p className="text-5xl mb-4">🔮</p>
            <p>Кәсіптер әлі қосылмаған</p>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selected && (
        <ProfessionModal
          profession={selected}
          onClose={() => setSelected(null)}
          onStart={handleStart}
        />
      )}
    </div>
  )
}
