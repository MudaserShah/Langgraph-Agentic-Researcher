/**
 * ThinkingPanel.tsx — Left dark-terminal panel showing real-time agent steps.
 *
 * Features:
 *   - Dark GitHub-style terminal background
 *   - JetBrains Mono font for the "code output" feel
 *   - AnimatePresence from Framer Motion — each step fades in as it arrives
 *   - Auto-scroll to the latest step
 *   - Pulsing "LIVE" indicator while the agent is running
 *
 * The auto-scroll uses a ref on a dummy div at the bottom of the list.
 * Every time `steps` changes (a new step is added), useEffect scrolls it
 * into view with smooth scrolling.
 */

import { AnimatePresence } from 'framer-motion'
import { useEffect, useRef } from 'react'
import type { ThinkingStep as ThinkingStepType } from '../../lib/types'
import { ThinkingEmptyState } from './EmptyState'
import { ThinkingStep } from './ThinkingStep'

interface ThinkingPanelProps {
  steps: ThinkingStepType[]
  isLive: boolean
}

export function ThinkingPanel({ steps, isLive }: ThinkingPanelProps) {
  // Ref for the bottom-sentinel div — used for auto-scrolling
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll whenever a new step is added
  useEffect(() => {
    if (steps.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [steps])

  return (
    <div className="flex flex-col h-full bg-terminal-bg border border-terminal-border rounded-xl overflow-hidden">

      {/* ── Panel header ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border bg-terminal-surface">
        <div className="flex items-center gap-2">
          {/* macOS-style traffic lights (purely decorative) */}
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
            <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
            <div className="w-3 h-3 rounded-full bg-[#28c840]" />
          </div>
          <span className="font-mono text-xs text-terminal-dim ml-1">
            agent.thinking_steps
          </span>
        </div>

        {/* Live indicator — pulsing green dot while streaming */}
        {isLive && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-terminal-green animate-pulse-dot" />
            <span className="font-mono text-xs text-terminal-green">LIVE</span>
          </div>
        )}
      </div>

      {/* ── Steps list ───────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto terminal-scrollbar p-4">
        {steps.length === 0 ? (
          <ThinkingEmptyState />
        ) : (
          <AnimatePresence initial={false}>
            {steps.map(step => (
              <ThinkingStep key={step.id} step={step} />
            ))}
          </AnimatePresence>
        )}

        {/* Bottom sentinel for auto-scroll */}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
