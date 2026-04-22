import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { lazy, Suspense } from 'react'
import Button from '../components/ui/Button'

const HeroScene = lazy(() => import('../components/three/HeroScene'))

const features = [
  {
    icon: '🤖',
    title: 'AI Кері байланыс',
    desc: 'Әр шешіміңізге жеке талдау мен нақты кеңестер алыңыз.',
  },
  {
    icon: '🎯',
    title: 'Нақты сценарийлер',
    desc: 'Кәсіби жағдайлардың шынайы модельдерімен жұмыс жасаңыз.',
  },
  {
    icon: '📈',
    title: 'Дағдыларды бақылау',
    desc: 'Прогресіңізді нақты уақытта қадағалаңыз және дамыңыз.',
  },
  {
    icon: '⚡',
    title: 'Жылдам нәтиже',
    desc: 'Бірнеше минутта нақты кәсіби тәжірибе алыңыз.',
  },
]

const stats = [
  { value: '50+', label: 'Сценарий' },
  { value: '10+', label: 'Кәсіп' },
  { value: '1000+', label: 'Пайдаланушы' },
  { value: '95%', label: 'Қанағаттану' },
]

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.5, delay }}
    >
      {children}
    </motion.div>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="relative bg-ogma-bg overflow-hidden">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center">
        {/* Background elements */}
        <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none" />
        <div className="orb w-[600px] h-[600px] bg-ogma-600 opacity-10 top-[-200px] left-[-200px]" />
        <div className="orb w-[400px] h-[400px] bg-ogma-accent opacity-8 bottom-[-100px] right-[-100px]" />

        <div className="page-container w-full grid md:grid-cols-2 gap-12 items-center py-24">
          {/* Left: text */}
          <div className="z-10">
            <motion.div
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                         border border-ogma-600/30 bg-ogma-600/10 text-ogma-400
                         text-xs font-semibold mb-6"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-ogma-accent animate-pulse" />
              AI-негізіндегі кәсіби симуляция
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-[1.05] mb-6"
            >
              Шешім<br />
              <span className="gradient-text">қабылдау</span><br />
              өнерін<br />
              меңгеріңіз
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg text-ogma-muted leading-relaxed mb-8 max-w-md"
            >
              Жасанды интеллект арқылы нақты жұмыс жағдайларын модельдеңіз
              және кәсіби дағдыларыңызды дамытыңыз.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap gap-3"
            >
              <Button size="lg" onClick={() => navigate('/professions')}>
                Бастау →
              </Button>
              <Button size="lg" variant="ghost" onClick={() => navigate('/register')}>
                Тіркелу
              </Button>
            </motion.div>
          </div>

          {/* Right: 3D scene */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative h-[480px] hidden md:block"
          >
            <div className="absolute inset-0 rounded-3xl overflow-hidden">
              <Suspense fallback={
                <div className="w-full h-full flex items-center justify-center">
                  <div className="w-24 h-24 rounded-full bg-ogma-600/20 animate-pulse" />
                </div>
              }>
                <HeroScene />
              </Suspense>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Stats ────────────────────────────────────────────────────────── */}
      <section className="py-12 border-y border-ogma-600/15">
        <div className="page-container grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((s, i) => (
            <FadeIn key={s.label} delay={i * 0.08}>
              <div className="text-center">
                <div className="text-4xl font-black gradient-text mb-1">{s.value}</div>
                <div className="text-sm text-ogma-muted">{s.label}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ── Features Bento ───────────────────────────────────────────────── */}
      <section className="py-24">
        <div className="page-container">
          <FadeIn>
            <div className="text-center mb-14">
              <h2 className="section-title mb-3">Неге <span className="gradient-text">OGMA</span>?</h2>
              <p className="text-ogma-muted max-w-md mx-auto">
                Кәсіби дамуда жаңа деңгейге шығыңыз
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((f, i) => (
              <FadeIn key={f.title} delay={i * 0.1}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="bento h-full group"
                >
                  <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300 inline-block">
                    {f.icon}
                  </div>
                  <h3 className="text-base font-bold text-ogma-text mb-2">{f.title}</h3>
                  <p className="text-sm text-ogma-muted leading-relaxed">{f.desc}</p>
                </motion.div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── Big CTA bento ────────────────────────────────────────────────── */}
      <section className="py-24">
        <div className="page-container">
          <FadeIn>
            <div className="relative overflow-hidden rounded-3xl border border-ogma-600/30
                            bg-gradient-to-br from-ogma-600/20 via-ogma-surface2 to-ogma-accent/10
                            p-12 md:p-16 text-center shadow-glow">
              <div className="orb w-64 h-64 bg-ogma-600 opacity-20 -top-20 -left-20" />
              <div className="orb w-48 h-48 bg-ogma-accent opacity-15 -bottom-16 -right-16" />
              <div className="relative z-10">
                <h2 className="text-4xl md:text-5xl font-black mb-4">
                  Бүгін <span className="gradient-text">бастаңыз</span>
                </h2>
                <p className="text-ogma-muted mb-8 text-lg max-w-md mx-auto">
                  Тіркелу тегін. Кез келген кәсіпті таңдаңыз және бірінші симуляцияңызды іске қосыңыз.
                </p>
                <Button size="lg" onClick={() => navigate('/register')}>
                  Тегін тіркелу →
                </Button>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ogma-600/15 py-8">
        <div className="page-container flex items-center justify-between">
          <span className="font-black text-lg">
            <span className="gradient-text">OGMA</span>
          </span>
          <p className="text-xs text-ogma-disabled">© 2024 OGMA. Барлық құқықтар сақталған.</p>
        </div>
      </footer>
    </div>
  )
}
