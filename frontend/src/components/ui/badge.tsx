/**
 * badge.tsx — Small pill-shaped label for status/category indicators.
 * Used for: sub-question pills, strategy labels, URL count, etc.
 */

import { cn } from '../../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'indigo' | 'green' | 'amber' | 'slate' | 'red'
  className?: string
}

export function Badge({ children, variant = 'indigo', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variant === 'indigo' && 'bg-indigo-50 text-indigo-700 border border-indigo-200',
        variant === 'green'  && 'bg-emerald-50 text-emerald-700 border border-emerald-200',
        variant === 'amber'  && 'bg-amber-50 text-amber-700 border border-amber-200',
        variant === 'slate'  && 'bg-slate-100 text-slate-600 border border-slate-200',
        variant === 'red'    && 'bg-red-50 text-red-700 border border-red-200',
        className,
      )}
    >
      {children}
    </span>
  )
}
