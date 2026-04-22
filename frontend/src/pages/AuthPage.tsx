import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import LoginForm from '../components/auth/LoginForm'
import RegisterForm from '../components/auth/RegisterForm'

export default function AuthPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState<'login' | 'register'>(
    location.pathname === '/register' ? 'register' : 'login',
  )

  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true })
  }, [user, navigate])

  useEffect(() => {
    setMode(location.pathname === '/register' ? 'register' : 'login')
  }, [location.pathname])

  function switchMode() {
    const next = mode === 'login' ? 'register' : 'login'
    setMode(next)
    navigate(`/${next}`, { replace: true })
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative">
      {/* Background */}
      <div className="absolute inset-0 bg-grid-pattern bg-grid pointer-events-none" />
      <div className="orb w-80 h-80 bg-ogma-600 opacity-15 top-[-60px] right-[-60px]" />
      <div className="orb w-64 h-64 bg-ogma-accent opacity-10 bottom-[-40px] left-[-40px]" />

      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative w-full max-w-md"
      >
        {/* Card */}
        <div className="glass-strong rounded-3xl p-8 shadow-glow-lg">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl
                            bg-gradient-primary shadow-glow mb-4">
              <span className="text-white font-black text-2xl">O</span>
            </div>
            <h1 className="text-2xl font-black text-ogma-text">
              {mode === 'login' ? 'Қош келдіңіз!' : 'Тіркелу'}
            </h1>
            <p className="text-sm text-ogma-muted mt-1">
              {mode === 'login'
                ? 'Аккаунтыңызға кіріңіз'
                : 'Жаңа аккаунт жасаңыз'}
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex p-1 bg-ogma-surface3 rounded-xl mb-6">
            {(['login', 'register'] as const).map(m => (
              <button
                key={m}
                onClick={() => { setMode(m); navigate(`/${m}`, { replace: true }) }}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all duration-200
                  ${mode === m
                    ? 'bg-ogma-600 text-white shadow-glow-sm'
                    : 'text-ogma-muted hover:text-ogma-secondary'
                  }`}
              >
                {m === 'login' ? 'Кіру' : 'Тіркелу'}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {mode === 'login' ? (
              <LoginForm key="login" onSwitch={switchMode} />
            ) : (
              <RegisterForm key="register" onSwitch={switchMode} />
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}
