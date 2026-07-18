/**
 * ResearchSummary.tsx — Quick audit card shown above the report.
 *
 * Displays a summary of what the agent did:
 *   - Sub-questions used
 *   - URLs searched
 *   - Strategy (web only or web + KB)
 *   - KB searched?
 *
 * This answers the student question: "How did the agent produce this?"
 */

import { CheckCircle2, Database, Globe, ListOrdered } from 'lucide-react'
import type { ResearchStats } from '../../lib/types'

interface ResearchSummaryProps {
  stats: ResearchStats
}

export function ResearchSummary({ stats }: ResearchSummaryProps) {
  return (
    <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <p className="text-sm font-semibold text-emerald-800">Research Complete</p>
      </div>

      {/* Stats row */}
      <div className="flex flex-wrap gap-3 mb-3">
        <StatPill icon={<Globe className="w-3 h-3" />} label={`${stats.urls_searched} URLs searched`} />
        <StatPill
          icon={<Database className="w-3 h-3" />}
          label={stats.kb_searched ? 'Knowledge base searched' : 'Web only'}
        />
        <StatPill
          icon={<ListOrdered className="w-3 h-3" />}
          label={`${stats.sub_questions.length} sub-questions`}
        />
      </div>

      {/* Sub-questions list */}
      {stats.sub_questions.length > 0 && (
        <div className="border-t border-emerald-200 pt-2.5 mt-2.5">
          <p className="text-xs text-emerald-700 font-medium mb-1.5">Queries sent to the web:</p>
          <div className="flex flex-col gap-1">
            {stats.sub_questions.map((q, i) => (
              <div key={i} className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-mono text-xs mt-0.5 flex-shrink-0">›</span>
                <span className="text-emerald-800 text-xs leading-snug">{q}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Small inline stat pill
function StatPill({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-1.5 text-emerald-700 text-xs bg-emerald-100 px-2.5 py-1 rounded-full">
      {icon}
      {label}
    </div>
  )
}
