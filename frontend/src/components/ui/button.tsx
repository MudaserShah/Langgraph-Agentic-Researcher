/**
 * button.tsx — Reusable Button component.
 *
 * This follows the "shadcn/ui" pattern:
 *   - A component wraps the native HTML element
 *   - `variant` prop selects a predefined style (primary, secondary, ghost)
 *   - `size` prop controls dimensions
 *   - `className` prop allows one-off overrides
 *   - `...props` passes through all native button attributes (disabled, onClick, type, etc.)
 *
 * The cn() utility from lib/utils.ts merges Tailwind classes safely.
 */

import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          // Base styles — always applied
          'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
          'transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'active:scale-[0.97]',

          // Size variants
          size === 'sm' && 'px-3 py-1.5 text-xs',
          size === 'md' && 'px-4 py-2 text-sm',
          size === 'lg' && 'px-6 py-3 text-base',

          // Color variants
          variant === 'primary' && [
            'bg-indigo-600 text-white hover:bg-indigo-700',
            'focus:ring-indigo-500',
          ],
          variant === 'secondary' && [
            'bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200',
            'focus:ring-slate-400',
          ],
          variant === 'ghost' && [
            'bg-transparent text-slate-600 hover:bg-slate-100',
            'focus:ring-slate-400',
          ],
          variant === 'danger' && [
            'bg-red-600 text-white hover:bg-red-700',
            'focus:ring-red-500',
          ],

          className,
        )}
        {...props}
      >
        {isLoading && (
          // Spinner shown when isLoading=true
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'

export { Button }
