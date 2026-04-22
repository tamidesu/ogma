import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import Button from '../ui/Button'

interface Props {
  onSwitch: () => void
}

export default function RegisterForm({ onSwitch }: Props) {
  const { register } = useAuth()
  const toast = useToast()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password.length < 8) {
      toast('Құпиясөз кемінде 8 таңбадан тұруы керек', 'warning')
      return
    }
    if (!/\d/.test(password)) {
      toast('Құпиясөз кемінде бір санды қамтуы керек', 'warning')
      return
    }
    setLoading(true)
    try {
      await register({
        email,
        password,
        display_name: displayName || undefined,
      })
      toast('Сәтті тіркелдіңіз!', 'success')
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
          Есімінгіз <span className="text-ogma-muted font-normal">(міндетті емес)</span>
        </label>
        <input
          type="text"
          value={displayName}
          onChange={e => setDisplayName(e.target.value)}
          placeholder="Аты-жөніңіз"
          maxLength={100}
          className="input-field"
        />
      </div>

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
          placeholder="Кемінде 8 таңба, бір сан"
          required
          className="input-field"
        />
        <p className="mt-1.5 text-xs text-ogma-muted">
          Кемінде 8 таңба және бір сан болуы керек
        </p>
      </div>

      <Button type="submit" loading={loading} className="w-full mt-1" size="lg">
        Тіркелу
      </Button>

      <p className="text-center text-sm text-ogma-muted">
        Тіркелгіңіз бар ма?{' '}
        <button
          type="button"
          onClick={onSwitch}
          className="text-ogma-400 hover:text-ogma-300 font-medium transition-colors"
        >
          Кіру
        </button>
      </p>
    </motion.form>
  )
}
