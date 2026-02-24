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

export function ClassificationBanner({ level, className }: ClassificationBannerProps) {
  const config = BANNER_CONFIG[level]
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
