import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const icons: Record<ToastType, string> = {
  success: '✓',
  error:   '✕',
  info:    'ℹ',
  warning: '⚠',
}

const colors: Record<ToastType, string> = {
  success: 'border-ogma-success/40 bg-ogma-success/10 text-ogma-success',
  error:   'border-ogma-error/40 bg-ogma-error/10 text-ogma-error',
  info:    'border-ogma-info/40 bg-ogma-info/10 text-ogma-info',
  warning: 'border-ogma-warning/40 bg-ogma-warning/10 text-ogma-warning',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-[400] flex flex-col gap-3 pointer-events-none">
        <AnimatePresence>
          {toasts.map(t => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 60, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 60, scale: 0.9 }}
              transition={{ type: 'spring', damping: 20, stiffness: 300 }}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl border glass-strong shadow-card-lg
                          pointer-events-auto min-w-[260px] max-w-sm ${colors[t.type]}`}
            >
              <span className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full
                               text-xs font-bold border border-current">
                {icons[t.type]}
              </span>
              <p className="text-sm font-medium text-ogma-text flex-1">{t.message}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx.toast
}
