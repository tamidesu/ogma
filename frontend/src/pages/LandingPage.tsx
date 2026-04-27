import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { lazy, Suspense, useState } from 'react'
import Button from '../components/ui/Button'
import ErrorBoundary from '../components/common/ErrorBoundary'

const HeroScene = lazy(() => import('../components/three/HeroScene'))

function HeroFallback() {
  return (
    <div className="w-full h-full flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-ogma-600/20 via-transparent to-ogma-accent/10" />
      <motion.div
        animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }}
        transition={{ repeat: Infinity, duration: 6, ease: 'easeInOut' }}
        className="w-56 h-56 rounded-full bg-gradient-to-br from-ogma-600/50 to-ogma-accent/30 blur-sm shadow-glow"
      />
      <motion.div
        animate={{ scale: [1.1, 1, 1.1], rotate: [0, -3, 3, 0] }}
        transition={{ repeat: Infinity, duration: 8, ease: 'easeInOut' }}
        className="absolute w-40 h-40 rounded-full border border-ogma-600/30 bg-ogma-600/10"
      />
    </div>
  )
}

const pillars = [
  {
    icon: '🧠',
    title: 'AI-генерация',
    desc: 'Жасанды интеллект нақты нормативтік құжаттар негізінде шынайы кейстер жасайды — медициналық хаттамалар, ҚНжЕ, кодекстер.',
    color: '#7c3aed',
  },
  {
    icon: '🎭',
    title: 'Әрекет еркіндігі',
    desc: 'Тест емес, тірі диалог. Құжаттармен жұмыс жасау, талдау жүргізу, сызбалар салу — механика кәсіпке байланысты.',
    color: '#3b82f6',
  },
  {
    icon: '💥',
    title: 'Тірі салдарлар',
    desc: 'Жүйе шешімдерді бағалап, шынайы нәтиже көрсетеді: клиенттің наразылығынан бастап кәсіби құлдырауға дейін.',
    color: '#ef4444',
  },
]

const professions = [
  {
    icon: '⚖️',
    name: 'Заңгер',
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg,#7c3aed,#f59e0b)',
    scenarios: [
      'Азаматтық процесс: дәлелдемелермен жұмыс, өтінішхаттар, клиентпен және оппонентпен қарым-қатынас',
      'Қылмыстық процесс: қылмыс құрамын талдау, куәларды жауап алу, сот пікірталастары',
      'Тірі диалог: куә қысым астында жауабын өзгертеді, клиент үрейленеді, судья ескерту жасайды',
    ],
  },
  {
    icon: '🩺',
    name: 'Дәрігер',
    color: '#06b6d4',
    gradient: 'linear-gradient(135deg,#7c3aed,#06b6d4)',
    scenarios: [
      'Жедел жағдай диагностикасы: науқасты тексеру, анализдер тағайындау, диагноз қою',
      'Операция жоспарлау: тәуекелдерді бағалау, команданы дайындау',
      'Науқаспен қарым-қатынас: қиын жаңалықтарды жеткізу, отбасымен жұмыс',
    ],
  },
  {
    icon: '💻',
    name: 'Бағдарламашы',
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg,#7c3aed,#3b82f6)',
    scenarios: [
      'Продакшн дағдарысы: серверлер құлады, клиент деректері қауіпте',
      'Архитектура таңдау: монолит пе, микросервис пе — команда бөлінген',
      'Техникалық борыш: жаңа фича қосу vs код рефакторинг',
    ],
  },
  {
    icon: '📊',
    name: 'Бизнес-менеджер',
    color: '#10b981',
    gradient: 'linear-gradient(135deg,#7c3aed,#10b981)',
    scenarios: [
      'Дағдарысты басқару: негізгі қызметкер кетуге ниетті, CEO үрейленген',
      'Жаңа жобаны іске қосу: бюджетті бөлу, команданы жинау',
      'Команда конфликтісі: екі бөлім арасындағы дауды шешу',
    ],
  },
]

const stats = [
  { value: '4', label: 'Кәсіп' },
  { value: '12+', label: 'Сценарий' },
  { value: '8–11', label: 'Сынып' },
  { value: '100%', label: 'Тегін' },
]

const competitors = [
  { category: 'Механика', analog: 'Сауалнамалар мен құрғақ теория', ours: 'Интерактивті бизнес-симуляция' },
  { category: 'Деректер базасы', analog: 'Жалпы ұсыныстар', ours: 'Нақты нормативтік құжаттар' },
  { category: 'Нәтиже', analog: 'Гипотетикалық кеңес', ours: 'Жеке тәжірибе «алаңда»' },
  { category: 'Ұстау', analog: 'Төмен (қызықсыз)', ours: 'Жоғары (геймификация)' },
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
  const [activeProfession, setActiveProfession] = useState(0)

  return (
    <div className="relative bg-ogma-bg overflow-hidden">
      {/* ── Hero ── */}
      <section className="relative min-h-screen flex items-center">
        <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none" />
        <div className="orb w-[600px] h-[600px] bg-ogma-600 opacity-10 top-[-200px] left-[-200px]" />
        <div className="orb w-[400px] h-[400px] bg-ogma-accent opacity-8 bottom-[-100px] right-[-100px]" />

        <div className="page-container w-full grid md:grid-cols-2 gap-12 items-center py-24">
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
              8–11 сынып оқушыларына арналған
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight leading-[1.1] mb-6"
            >
              Болашақ кәсібіңді<br />
              <span className="gradient-text">«татып көр»</span><br />
              қауіпсіз ортада
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg text-ogma-muted leading-relaxed mb-4 max-w-lg"
            >
              OGMA — кәсіби қызметтің интерактивті симуляторы.
              Бұл тест емес, лекция емес. <strong className="text-ogma-secondary">Бұл тірі жағдайлар</strong>, мұнда сіздің
              әр әрекетіңіз оқиғаның дамуы мен оның финалына әсер етеді.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap gap-3"
            >
              <Button size="lg" onClick={() => navigate('/register')}>
                Тегін бастау →
              </Button>
              <Button size="lg" variant="ghost" onClick={() => navigate('/login')}>
                Кіру
              </Button>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative h-[480px] hidden md:block"
          >
            <div className="absolute inset-0 rounded-3xl overflow-hidden">
              <ErrorBoundary fallback={<HeroFallback />}>
                <Suspense fallback={
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="w-24 h-24 rounded-full bg-ogma-600/20 animate-pulse" />
                  </div>
                }>
                  <HeroScene />
                </Suspense>
              </ErrorBoundary>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Stats ── */}
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

      {/* ── How it works (3 pillars) ── */}
      <section className="py-24">
        <div className="page-container">
          <FadeIn>
            <div className="text-center mb-14">
              <h2 className="section-title mb-3">
                Платформа <span className="gradient-text">қалай жұмыс істейді?</span>
              </h2>
              <p className="text-ogma-muted max-w-lg mx-auto">
                Тест емес, тірі жағдайлар. Әр шешіміңіз нәтижеге әсер етеді.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-6">
            {pillars.map((p, i) => (
              <FadeIn key={p.title} delay={i * 0.12}>
                <motion.div
                  whileHover={{ y: -6, scale: 1.02 }}
                  className="bento h-full group relative overflow-hidden"
                >
                  <div
                    className="absolute top-0 left-0 w-full h-1 rounded-t-2xl"
                    style={{ background: p.color }}
                  />
                  <div className="text-4xl mb-5 group-hover:scale-110 transition-transform duration-300 inline-block">
                    {p.icon}
                  </div>
                  <h3 className="text-lg font-bold text-ogma-text mb-3">{p.title}</h3>
                  <p className="text-sm text-ogma-muted leading-relaxed">{p.desc}</p>
                </motion.div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── Professions showcase ── */}
      <section className="py-24">
        <div className="page-container">
          <FadeIn>
            <div className="text-center mb-14">
              <h2 className="section-title mb-3">
                <span className="gradient-text">Кәсіптер</span> мысалдары
              </h2>
              <p className="text-ogma-muted max-w-lg mx-auto">
                Әр кәсіптің өз механикасы, өз кейстері, өз персонаждары бар
              </p>
            </div>
          </FadeIn>

          {/* Profession tabs */}
          <div className="flex flex-wrap justify-center gap-3 mb-10">
            {professions.map((prof, i) => (
              <motion.button
                key={prof.name}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setActiveProfession(i)}
                style={{
                  background: activeProfession === i
                    ? prof.gradient
                    : 'rgba(28,22,64,0.5)',
                  border: `1px solid ${activeProfession === i ? prof.color + '80' : 'rgba(124,58,237,0.2)'}`,
                  color: activeProfession === i ? '#fff' : '#a78bfa',
                  padding: '10px 22px',
                  borderRadius: 14,
                  fontSize: 15,
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all 0.3s',
                }}
              >
                <span style={{ fontSize: 20 }}>{prof.icon}</span>
                {prof.name}
              </motion.button>
            ))}
          </div>

          {/* Active profession details */}
          <motion.div
            key={activeProfession}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="bento relative overflow-hidden"
            style={{ borderColor: professions[activeProfession].color + '40' }}
          >
            <div
              className="absolute top-0 left-0 w-full h-1"
              style={{ background: professions[activeProfession].gradient }}
            />
            <div className="flex items-center gap-4 mb-6">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl"
                style={{
                  background: professions[activeProfession].color + '20',
                  border: `1px solid ${professions[activeProfession].color}40`,
                }}
              >
                {professions[activeProfession].icon}
              </div>
              <div>
                <h3 className="text-xl font-black text-ogma-text">
                  {professions[activeProfession].name}
                </h3>
                <p className="text-xs text-ogma-muted">Интерактивті сценарийлер</p>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              {professions[activeProfession].scenarios.map((sc, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="p-4 rounded-xl"
                  style={{
                    background: professions[activeProfession].color + '0a',
                    border: `1px solid ${professions[activeProfession].color}20`,
                  }}
                >
                  <div className="flex items-start gap-3">
                    <span
                      className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mt-0.5"
                      style={{ background: professions[activeProfession].gradient }}
                    >
                      {i + 1}
                    </span>
                    <p className="text-sm text-ogma-secondary leading-relaxed">{sc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Competitors comparison ── */}
      <section className="py-24">
        <div className="page-container">
          <FadeIn>
            <div className="text-center mb-14">
              <h2 className="section-title mb-3">
                Неліктен <span className="gradient-text">аналогтар емес?</span>
              </h2>
              <p className="text-ogma-muted max-w-lg mx-auto">
                Mansap Kompasy, Tanu.AI, Capitalism Lab — олар не ұсынады?
              </p>
            </div>
          </FadeIn>

          <FadeIn delay={0.1}>
            <div className="bento overflow-hidden p-0">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'rgba(124,58,237,0.15)' }}>
                    <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: 13, fontWeight: 700, color: '#a78bfa', borderBottom: '1px solid rgba(124,58,237,0.2)' }}>
                      Категория
                    </th>
                    <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: 13, fontWeight: 700, color: '#7c6fa8', borderBottom: '1px solid rgba(124,58,237,0.2)' }}>
                      Аналогтар
                    </th>
                    <th style={{ padding: '14px 20px', textAlign: 'left', fontSize: 13, fontWeight: 700, color: '#10b981', borderBottom: '1px solid rgba(124,58,237,0.2)' }}>
                      OGMA ✨
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {competitors.map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(124,58,237,0.1)' }}>
                      <td style={{ padding: '13px 20px', fontSize: 13, fontWeight: 600, color: '#c4b5fd' }}>
                        {row.category}
                      </td>
                      <td style={{ padding: '13px 20px', fontSize: 13, color: '#7c6fa8' }}>
                        {row.analog}
                      </td>
                      <td style={{ padding: '13px 20px', fontSize: 13, color: '#10b981', fontWeight: 600 }}>
                        {row.ours}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Big CTA ── */}
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
                  Тіркелу тегін. Кәсіпті таңдаңыз, симуляцияны бастаңыз, болашақ мамандығыңызды сезініңіз.
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
          <p className="text-xs text-ogma-disabled">© 2026 OGMA. Барлық құқықтар сақталған.</p>
        </div>
      </footer>
    </div>
  )
}
