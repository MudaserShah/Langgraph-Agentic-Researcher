/**
 * switch.tsx — Toggle switch component (styled checkbox).
 * Used for the "Force web search" toggle in the research input bar.
 */

import { cn } from '../../lib/utils'

interface SwitchProps {
  checked: boolean
  onCheckedChange: (checked: boolean) => void
  id?: string
  label?: string
  disabled?: boolean
}

export function Switch({ checked, onCheckedChange, id, label, disabled }: SwitchProps) {
  return (
    <label
      htmlFor={id}
      className={cn(
        'inline-flex items-center gap-2 cursor-pointer select-none',
        disabled && 'opacity-50 cursor-not-allowed',
      )}
    >
      {/* Hidden checkbox for accessibility */}
      <input
        id={id}
        type="checkbox"
        className="sr-only"
        checked={checked}
        disabled={disabled}
        onChange={e => onCheckedChange(e.target.checked)}
      />

      {/* Visual toggle track */}
      <div
        className={cn(
          'relative w-9 h-5 rounded-full transition-colors duration-200',
          checked ? 'bg-indigo-600' : 'bg-slate-300',
        )}
      >
        {/* Sliding circle (thumb) */}
        <div
          className={cn(
            'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow',
            'transition-transform duration-200',
            checked && 'translate-x-4',
          )}
        />
      </div>

      {label && (
        <span className="text-sm text-slate-600 font-medium">{label}</span>
      )}
    </label>
  )
}
