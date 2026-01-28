import './SkeletonLoader.css'

interface SkeletonLoaderProps {
  width?: string
  height?: string
  className?: string
}

export function SkeletonLoader({ width, height, className = '' }: SkeletonLoaderProps) {
  return <div className={`skeleton ${className}`} style={{ width, height }} />
}
