import { useMemo } from 'react'

interface Props {
  color?: string
  count?: number
}

export default function Particles({ color = '#7c3aed', count = 12 }: Props) {
  const particles = useMemo(
    () =>
      Array.from({ length: count }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: 2 + Math.random() * 4,
        dur: 4 + Math.random() * 6,
        delay: Math.random() * 4,
      })),
    [count],
  )

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden>
      {particles.map(p => (
        <span
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: color,
            opacity: 0.5,
            animation: `particleFloat ${p.dur}s ${p.delay}s ease-in-out infinite`,
            boxShadow: `0 0 ${p.size * 2}px ${color}`,
          }}
        />
      ))}
    </div>
  )
}
