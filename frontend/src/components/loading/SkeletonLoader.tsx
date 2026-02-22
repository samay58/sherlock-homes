import './SkeletonLoader.css'

interface SkeletonLoaderProps {
  width?: string
  height?: string
  className?: string
}

export function SkeletonLoader({ width, height, className = '' }: SkeletonLoaderProps) {
  return (
    <div aria-live="polite" aria-busy="true">
      <span className="sr-only">Loading...</span>
      <div className={`skeleton ${className}`} style={{ width, height }} aria-hidden="true" />
    </div>
  )
}
