import type { ProfessionCharacter, CharacterStatus } from '../../lib/professionVisuals'
import { STATUS_CONFIG } from '../../lib/professionVisuals'

interface Props {
  char: ProfessionCharacter & { status: CharacterStatus }
  message?: string
}

export default function CharacterCard({ char, message }: Props) {
  const cfg = STATUS_CONFIG[char.status] ?? STATUS_CONFIG.watching

  return (
    <div
      style={{
        flex: 1, minWidth: 0,
        padding: '13px 14px',
        borderRadius: 16,
        background: 'rgba(20,15,46,0.82)',
        border: `1px solid ${cfg.color}30`,
        backdropFilter: 'blur(12px)',
        transition: 'all 0.4s ease',
        boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: message ? 8 : 0 }}>
        {/* Avatar + status dot */}
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <span style={{ fontSize: 26 }}>{char.avatar}</span>
          <div
            style={{
              position: 'absolute', bottom: -2, right: -2,
              width: 10, height: 10, borderRadius: '50%',
              background: cfg.color,
              border: '2px solid #07040f',
              animation: cfg.pulse ? 'charPulse 1.5s ease-in-out infinite' : 'none',
            }}
          />
        </div>

        <div style={{ minWidth: 0, flex: 1 }}>
          <p style={{ fontSize: 11, fontWeight: 700, color: '#f5f0ff', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {char.name}
          </p>
          <p style={{ fontSize: 10, color: '#7c6fa8', margin: 0 }}>{char.role}</p>
        </div>

        <span
          style={{
            fontSize: 9, fontWeight: 700,
            color: cfg.color,
            background: `${cfg.color}18`,
            padding: '2px 7px', borderRadius: 99,
            border: `1px solid ${cfg.color}30`,
            flexShrink: 0,
            whiteSpace: 'nowrap',
          }}
        >
          {cfg.label}
        </span>
      </div>

      {message && (
        <div
          style={{
            fontSize: 11, color: '#c4b5fd',
            fontStyle: 'italic', lineHeight: 1.5,
            paddingTop: 8,
            borderTop: '1px solid rgba(124,58,237,0.1)',
          }}
        >
          "{message}"
        </div>
      )}
    </div>
  )
}
