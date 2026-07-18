/**
 * input.tsx — Styled text input component.
 * Wraps the native <input> element with consistent Tailwind styling.
 */

import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

type InputProps = React.InputHTMLAttributes<HTMLInputElement>

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          'flex w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5',
          'text-sm text-slate-900 placeholder:text-slate-400',
          'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-shadow duration-150',
          className,
        )}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'

export { Input }
