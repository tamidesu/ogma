type Variant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent'

interface Props {
  children: React.ReactNode
  variant?: Variant
  size?: 'sm' | 'md'
  dot?: boolean
}

const variantClasses: Record<Variant, string> = {
  default: 'bg-ogma-600/20 text-ogma-300 border-ogma-600/30',
  success: 'bg-ogma-success/15 text-ogma-success border-ogma-success/30',
  warning: 'bg-ogma-warning/15 text-ogma-warning border-ogma-warning/30',
  error:   'bg-ogma-error/15 text-ogma-error border-ogma-error/30',
  info:    'bg-ogma-info/15 text-ogma-info border-ogma-info/30',
  accent:  'bg-ogma-accent/15 text-ogma-accent border-ogma-accent/30',
}

const dotColors: Record<Variant, string> = {
  default: 'bg-ogma-400',
  success: 'bg-ogma-success',
  warning: 'bg-ogma-warning',
  error:   'bg-ogma-error',
  info:    'bg-ogma-info',
  accent:  'bg-ogma-accent',
}

export default function Badge({ children, variant = 'default', size = 'sm', dot = false }: Props) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium border rounded-full
        ${size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm'}
        ${variantClasses[variant]}
      `}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotColors[variant]}`} />}
      {children}
    </span>
  )
}
