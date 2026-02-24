import { clsx } from 'clsx'

interface LoadingSpinnerProps {
  fullscreen?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const SIZE_CLASSES = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-4',
}

export function LoadingSpinner({ fullscreen, size = 'md', className }: LoadingSpinnerProps) {
  const spinner = (
    <div
      role="status"
      aria-label="Loading"
      className={clsx(
        'rounded-full border-sky-400 border-t-transparent animate-spin',
        SIZE_CLASSES[size],
        className,
      )}
    />
  )

  if (fullscreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-gray-950/80 z-50">
        {spinner}
      </div>
    )
  }

  return spinner
}
