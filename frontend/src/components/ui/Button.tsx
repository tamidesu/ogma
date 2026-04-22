import { motion } from 'framer-motion'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'ghost' | 'outline' | 'danger'
type Size    = 'sm' | 'md' | 'lg'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
  icon?: ReactNode
  children: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-ogma-600 hover:bg-ogma-700 text-white shadow-glow-sm hover:shadow-glow border border-ogma-500/30',
  ghost:   'bg-ogma-surface2/60 hover:bg-ogma-surface2 border border-ogma-600/20 hover:border-ogma-600/50 text-ogma-secondary',
  outline: 'bg-transparent border border-ogma-600/50 hover:border-ogma-600 text-ogma-400 hover:text-ogma-300',
  danger:  'bg-ogma-error/10 hover:bg-ogma-error/20 border border-ogma-error/40 text-ogma-error',
}

const sizeClasses: Record<Size, string> = {
  sm: 'px-3.5 py-2 text-sm gap-1.5 rounded-lg',
  md: 'px-5 py-2.5 text-sm gap-2 rounded-xl',
  lg: 'px-7 py-3.5 text-base gap-2.5 rounded-xl',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  disabled,
  className = '',
  ...rest
}: Props) {
  return (
    <motion.button
      whileHover={{ scale: disabled || loading ? 1 : 1.02 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center font-semibold
        transition-all duration-200 backdrop-blur-sm
        disabled:opacity-40 disabled:cursor-not-allowed
        ${variantClasses[variant]} ${sizeClasses[size]} ${className}
      `}
      {...(rest as object)}
    >
      {loading ? (
        <svg className="animate-spin h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ) : icon}
      {children}
    </motion.button>
  )
}
