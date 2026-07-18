/**
 * HistoryCard.tsx — One card in the history list.
 *
 * Shows: topic, date, URL count badge.
 * Actions: View (loads full report into research panel), PDF download, Delete.
 */

import { Download, Eye, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { downloadPdf } from '../../lib/api'
import { formatDate } from '../../lib/utils'
import type { HistoryItem } from '../../lib/types'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'

interface HistoryCardProps {
  item: HistoryItem
  onView: (id: string) => void
  onDelete: (id: string) => void
}

export function HistoryCard({ item, onView, onDelete }: HistoryCardProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      await downloadPdf(item.id, item.topic)
    } catch {
      alert('PDF download failed.')
    } finally {
      setIsDownloading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Delete this report?')) return
    setIsDeleting(true)
    onDelete(item.id)
  }

  return (
    <div className="flex items-start gap-4 p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-200 hover:shadow-sm transition-all duration-150">

      {/* Icon */}
      <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-lg">
        📄
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <h3 className="text-slate-800 font-medium text-sm leading-snug mb-1 truncate">
          {item.topic}
        </h3>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-slate-400 text-xs">{formatDate(item.created_at)}</span>
          <Badge variant="indigo">{item.url_count} URLs</Badge>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <Button variant="secondary" size="sm" onClick={() => onView(item.id)}>
          <Eye className="w-3.5 h-3.5" />
          View
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleDownload}
          isLoading={isDownloading}
          title="Download PDF"
        >
          <Download className="w-3.5 h-3.5" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          isLoading={isDeleting}
          className="text-red-500 hover:text-red-700 hover:bg-red-50"
          title="Delete report"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  )
}
