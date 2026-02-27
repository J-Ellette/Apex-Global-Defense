import { clsx } from 'clsx'
import type { ClassificationLevel } from '../../shared/api/types'

interface ClassificationBannerProps {
  level: ClassificationLevel
  className?: string
}

const BANNER_CONFIG: Record<ClassificationLevel, { label: string; className: string }> = {
  UNCLASS:    { label: 'UNCLASSIFIED',                    className: 'banner-unclass' },
  FOUO:       { label: 'UNCLASSIFIED // FOR OFFICIAL USE ONLY', className: 'banner-fouo' },
  SECRET:     { label: 'SECRET',                          className: 'banner-secret' },
  TOP_SECRET: { label: 'TOP SECRET',                      className: 'banner-top-secret' },
  TS_SCI:     { label: 'TOP SECRET // SCI',               className: 'banner-ts-sci' },
}

const NUMERIC_CLASSIFICATION_MAP: Record<number, ClassificationLevel> = {
  0: 'UNCLASS',
  1: 'FOUO',
  2: 'SECRET',
  3: 'TOP_SECRET',
  4: 'TS_SCI',
}

function normalizeClassificationLevel(level: ClassificationLevel | number): ClassificationLevel {
  if (typeof level === 'number') {
    return NUMERIC_CLASSIFICATION_MAP[level] ?? 'UNCLASS'
  }
  if (level in BANNER_CONFIG) {
    return level
  }
  return 'UNCLASS'
}

export function ClassificationBanner({ level, className }: ClassificationBannerProps) {
  const normalized = normalizeClassificationLevel(level as ClassificationLevel | number)
  const config = BANNER_CONFIG[normalized]
  return (
    <div
      role="banner"
      aria-label={`Classification: ${config.label}`}
      className={clsx(
        'text-center text-xs font-bold tracking-widest py-1 px-4 select-none',
        config.className,
        className,
      )}
    >
      {config.label}
    </div>
  )
}
