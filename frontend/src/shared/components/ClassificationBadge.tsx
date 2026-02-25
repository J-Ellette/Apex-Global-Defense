import { clsx } from 'clsx'
import type { ClassificationLevel } from '../api/types'

interface ClassificationBadgeProps {
  level: ClassificationLevel
  className?: string
}

const BADGE_CONFIG: Record<ClassificationLevel, { label: string; className: string }> = {
  UNCLASS:    { label: 'UNCLASS',    className: 'bg-green-900 text-green-200 border-green-700' },
  FOUO:       { label: 'FOUO',       className: 'bg-blue-900 text-blue-200 border-blue-700' },
  SECRET:     { label: 'SECRET',     className: 'bg-red-900 text-red-200 border-red-700' },
  TOP_SECRET: { label: 'TOP SECRET', className: 'bg-orange-900 text-orange-200 border-orange-700' },
  TS_SCI:     { label: 'TS//SCI',    className: 'bg-yellow-800 text-yellow-100 border-yellow-600' },
}

export function ClassificationBadge({ level, className }: ClassificationBadgeProps) {
  const config = BADGE_CONFIG[level]
  return (
    <span
      className={clsx(
        'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider border select-none',
        config.className,
        className,
      )}
      title={`Classification: ${level}`}
    >
      {config.label}
    </span>
  )
}
