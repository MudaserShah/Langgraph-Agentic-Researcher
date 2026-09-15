/**
 * utils.ts — Shared utility functions.
 *
 * cn() — className utility
 *   Combines clsx (conditional class names) with tailwind-merge (deduplication).
 *   This is a standard pattern in Tailwind + React projects.
 *
 *   Problem it solves:
 *     <div className={`text-red-500 ${isActive ? 'text-blue-500' : ''}`}>
 *     → Both text-red-500 AND text-blue-500 are in the DOM. Which one wins?
 *       (CSS specificity rules apply — confusing!)
 *
 *   With cn():
 *     <div className={cn('text-red-500', isActive && 'text-blue-500')}>
 *     → tailwind-merge removes text-red-500 when text-blue-500 is added.
 *       The last class always wins. Predictable!
 *
 * formatDate() — formats ISO timestamps for display
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind CSS class names safely.
 * Usage: cn('px-4 py-2', isActive && 'bg-blue-500', className)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format an ISO timestamp into a readable date string.
 * "2025-04-14T16:30:00" → "Apr 14, 2025, 4:30 PM"
 */
export function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  } catch {
    return isoString
  }
}
