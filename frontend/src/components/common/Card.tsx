import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  glow?: boolean
}

export function Card({ children, className = '', glow = false }: CardProps) {
  return (
    <div
      className={`glass-panel rounded-2xl p-5 ${glow ? 'glow-accent' : ''} ${className}`}
    >
      {children}
    </div>
  )
}
