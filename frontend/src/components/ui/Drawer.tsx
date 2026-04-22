import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'

interface Props {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  side?: 'right' | 'left'
  width?: string
}

export default function Drawer({
  open,
  onClose,
  title,
  children,
  side = 'right',
  width = 'w-[420px]',
}: Props) {
  const xFrom = side === 'right' ? '100%' : '-100%'

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[300] flex">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-ogma-bg/70 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ x: xFrom }}
            animate={{ x: 0 }}
            exit={{ x: xFrom }}
            transition={{ type: 'spring', damping: 28, stiffness: 280 }}
            className={`
              absolute ${side}-0 top-0 h-full ${width} max-w-full
              glass-strong border-${side === 'right' ? 'l' : 'r'} border-ogma-600/30
              shadow-glow flex flex-col overflow-hidden
            `}
          >
            {title && (
              <div className="flex items-center justify-between px-6 py-5 border-b border-ogma-600/20">
                <h2 className="text-lg font-bold text-ogma-text">{title}</h2>
                <button
                  onClick={onClose}
                  className="w-8 h-8 flex items-center justify-center rounded-lg
                             text-ogma-muted hover:text-ogma-text hover:bg-ogma-surface3
                             transition-colors duration-150"
                >
                  ✕
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto p-6">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
