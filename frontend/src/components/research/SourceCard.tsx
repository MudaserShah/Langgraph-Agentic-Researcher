/**
 * SourceCard.tsx — Displays one web source at the bottom of the report.
 *
 * Shows: numbered badge, title (clickable link), URL, content preview.
 */

import { ExternalLink } from 'lucide-react'
import type { Source } from '../../lib/types'

interface SourceCardProps {
  source: Source
  index: number
}

export function SourceCard({ source, index }: SourceCardProps) {
  return (
    <div className="flex gap-3 p-3 rounded-lg border border-slate-100 hover:border-slate-200 hover:bg-slate-50 transition-colors duration-150">
      {/* Number badge */}
      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-200 text-slate-600 text-xs font-bold flex items-center justify-center mt-0.5">
        {index + 1}
      </div>

      <div className="flex-1 min-w-0">
        {/* Title — links to the source */}
        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-indigo-700 hover:text-indigo-900 font-medium text-sm mb-0.5 group"
        >
          <span className="truncate">{source.title || source.url}</span>
          <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
        </a>

        {/* URL */}
        <p className="text-slate-400 text-xs truncate mb-1">
          {source.url}
        </p>

        {/* Content preview */}
        {source.content_preview && (
          <p className="text-slate-600 text-xs leading-relaxed line-clamp-2">
            {source.content_preview}
          </p>
        )}
      </div>
    </div>
  )
}
