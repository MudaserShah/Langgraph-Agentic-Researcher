/**
 * ThinkingStep.tsx — A single step row in the Agent Thinking panel.
 *
 * There are two kinds of rows:
 *   isHeader=true  → "NODE HEADER" row (e.g. "🌐 Web Search")
 *                    Bold, coloured left border, node icon
 *   isHeader=false → "DETAIL" row (e.g. "  🔍 Query: 'AI in healthcare'")
 *                    Indented, dimmer text
 *
 * ANIMATION: Framer Motion animates each step in with opacity + slide-up.
 * This replaces the double-requestAnimationFrame trick from the original app.js.
 *
 * Why Framer Motion instead of CSS transitions?
 *   - enter/exit animations are declarative (initial/animate/exit props)
 *   - AnimatePresence in the parent handles mounting/unmounting
 *   - No need to manually toggle CSS classes or use refs
 */

import { motion } from 'framer-motion'
import { NODE_CONFIG } from '../../lib/constants'
import type { ThinkingStep as ThinkingStepType } from '../../lib/types'

interface ThinkingStepProps {
  step: ThinkingStepType
}

export function ThinkingStep({ step }: ThinkingStepProps) {
  const config = NODE_CONFIG[step.node]

  if (step.isHeader) {
    // ── Node header row ──────────────────────────────────────────────────────
    const Icon = config.Icon

    return (
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="flex items-center gap-2 mt-3 mb-1 pt-3 first:mt-0 first:pt-0"
        style={{ borderLeft: `3px solid ${config.color}`, paddingLeft: '10px' }}
      >
        <Icon
          className="w-3.5 h-3.5 flex-shrink-0"
          style={{ color: config.color }}
        />
        <span
          className="font-mono text-xs font-semibold uppercase tracking-wider"
          style={{ color: config.color }}
        >
          {config.label}
        </span>
      </motion.div>
    )
  }

  // ── Detail / thinking row ─────────────────────────────────────────────────
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="font-mono text-xs text-terminal-dim leading-relaxed pl-4 py-0.5"
    >
      {step.message}
    </motion.div>
  )
}
