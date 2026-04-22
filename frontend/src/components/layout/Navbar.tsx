import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import Button from '../ui/Button'

const navLinks = [
  { label: 'Кәсіптер', href: '/professions' },
  { label: 'Панель', href: '/dashboard', auth: true },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  async function handleLogout() {
    await logout()
    toast('Сәтті шықтыңыз', 'info')
    navigate('/')
  }

  const links = navLinks.filter(l => !l.auth || user)

  return (
    <header className="fixed top-0 left-0 right-0 z-[200]">
      <div className="glass-strong border-b border-ogma-600/20">
        <div className="page-container flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center
                            shadow-glow-sm group-hover:shadow-glow transition-all duration-300">
              <span className="text-white font-black text-sm">O</span>
            </div>
            <span className="font-black text-xl tracking-tight">
              <span className="gradient-text">OGM</span>
              <span className="text-ogma-text">A</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {links.map(l => (
              <Link
                key={l.href}
                to={l.href}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150
                  ${location.pathname.startsWith(l.href)
                    ? 'text-ogma-400 bg-ogma-600/15'
                    : 'text-ogma-muted hover:text-ogma-secondary hover:bg-ogma-surface3'
                  }`}
              >
                {l.label}
              </Link>
            ))}
          </nav>

          {/* Auth actions */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-ogma-muted">
                  {user.display_name ?? user.email.split('@')[0]}
                </span>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  Шығу
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                  Кіру
                </Button>
                <Button size="sm" onClick={() => navigate('/register')}>
                  Тіркелу
                </Button>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden w-9 h-9 flex flex-col items-center justify-center gap-1.5
                       rounded-lg hover:bg-ogma-surface3 transition-colors"
            onClick={() => setMenuOpen(v => !v)}
          >
            <span className={`w-5 h-0.5 bg-ogma-secondary transition-transform duration-200 ${menuOpen ? 'rotate-45 translate-y-2' : ''}`} />
            <span className={`w-5 h-0.5 bg-ogma-secondary transition-opacity duration-200 ${menuOpen ? 'opacity-0' : ''}`} />
            <span className={`w-5 h-0.5 bg-ogma-secondary transition-transform duration-200 ${menuOpen ? '-rotate-45 -translate-y-2' : ''}`} />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="md:hidden glass-strong border-b border-ogma-600/20 px-4 py-4 flex flex-col gap-2"
          >
            {links.map(l => (
              <Link
                key={l.href}
                to={l.href}
                onClick={() => setMenuOpen(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-medium text-ogma-secondary
                           hover:bg-ogma-surface3 transition-colors"
              >
                {l.label}
              </Link>
            ))}
            <div className="border-t border-ogma-600/20 mt-2 pt-3 flex flex-col gap-2">
              {user ? (
                <Button variant="ghost" onClick={handleLogout}>Шығу</Button>
              ) : (
                <>
                  <Button variant="ghost" onClick={() => { navigate('/login'); setMenuOpen(false) }}>Кіру</Button>
                  <Button onClick={() => { navigate('/register'); setMenuOpen(false) }}>Тіркелу</Button>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
