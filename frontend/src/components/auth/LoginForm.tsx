import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import Button from '../ui/Button'

interface Props {
  onSwitch: () => void
}

export default function LoginForm({ onSwitch }: Props) {
  const { login } = useAuth()
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await login({ email, password })
      toast('Сәтті кірдіңіз!', 'success')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Қате орын алды'
      toast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="flex flex-col gap-4"
    >
      <div>
        <label className="block text-sm font-medium text-ogma-secondary mb-1.5">
          Электрондық пошта
        </label>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
          className="input-field"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-ogma-secondary mb-1.5">
          Құпиясөз
        </label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="••••••••"
          required
          className="input-field"
        />
      </div>

      <Button type="submit" loading={loading} className="w-full mt-1" size="lg">
        Кіру
      </Button>

      <p className="text-center text-sm text-ogma-muted">
        Тіркелгіңіз жоқ па?{' '}
        <button
          type="button"
          onClick={onSwitch}
          className="text-ogma-400 hover:text-ogma-300 font-medium transition-colors"
        >
          Тіркелу
        </button>
      </p>
    </motion.form>
  )
}
